import time
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import ProductModel, ProductUnit, ScanLog, TransferHistory, Category
from .forms import ProductModelForm, GenerateUnitsForm, TransferForm
from .qr_utils import generate_qr
from .geo_utils import get_client_ip, get_location
from .verification import verify
from .alert_utils import alert_suspicious_scan
from blockchain.engine import generate_product_hash, generate_unit_serial
from blockchain.service import add_block, validate_chain, get_unit_history
from accounts.models import User


# ── Public home ──────────────────────────────────────────────────────────────

def home(request):
    features = [
        ("🔐", "Immutable SHA-256 Records",
         "Every product unit hashed and chained. Tampering any block invalidates the entire chain instantly."),
        ("📱", "QR Code Verification",
         "Customer scans QR → real-time GENUINE / SUSPICIOUS / FAKE verdict with full blockchain history."),
        ("🌍", "Geo Clone Detection",
         "IPInfo API locates every scan. Same QR from 3+ countries in 60 min = automatic cloning alert."),
        ("📧", "Instant Manufacturer Alerts",
         "SendGrid email + Twilio SMS fires the moment suspicious scan is detected. Zero manual monitoring."),
        ("⛓️", "Proof-of-Work Consensus",
         "Each block mined with PoW (difficulty 2) before accepted. Prevents rapid fake block injection."),
        ("👥", "3-Role Supply Chain",
         "Manufacturer → Distributor → Customer. Every custody transfer is an immutable on-chain event."),
    ]
    steps = [
        ("Manufacturer registers product model", "Brand, name, model code, category"),
        ("Generate physical units", "Each unit: serial + SHA-256 + QR image + blockchain record"),
        ("Distribute via supply chain", "Every transfer logged on-chain with actor identity + timestamp"),
        ("Customer scans QR", "3-check verification → instant verdict + geo location logged"),
    ]
    return render(request, "home.html", {"features": features, "steps": steps})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    ctx  = {"user": user}
    if user.is_manufacturer():
        ctx["models"]       = ProductModel.objects.filter(manufacturer=user).order_by("-created_at")
        ctx["total_units"]  = ProductUnit.objects.filter(model__manufacturer=user).count()
        ctx["flagged"]      = ProductUnit.objects.filter(model__manufacturer=user, status="FLAGGED").count()
        ctx["recent_scans"] = ScanLog.objects.filter(
            unit__model__manufacturer=user).order_by("-scanned_at")[:10]
    elif user.is_distributor():
        ctx["owned_units"] = ProductUnit.objects.filter(current_owner=user).order_by("-updated_at")
    else:
        ctx["scan_history"] = ScanLog.objects.filter(scanner_user=user).order_by("-scanned_at")[:20]
    return render(request, "dashboard.html", ctx)


# ── Product Model ─────────────────────────────────────────────────────────────

@login_required
def create_product_model(request):
    if not request.user.is_manufacturer():
        messages.error(request, "Only manufacturers can register product models.")
        return redirect("dashboard")
    form = ProductModelForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        pm              = form.save(commit=False)
        pm.manufacturer = request.user
        pm.save()
        messages.success(request, f"Product model '{pm.name}' registered successfully.")
        return redirect("product_model_detail", pk=pm.pk)
    return render(request, "products/product_model_form.html",
                  {"form": form, "title": "Register New Product Model"})


@login_required
def product_model_detail(request, pk):
    pm    = get_object_or_404(ProductModel, pk=pk, manufacturer=request.user)
    units = pm.units.all().order_by("-created_at")
    return render(request, "products/product_model_detail.html", {"pm": pm, "units": units})


# ── Generate Units ────────────────────────────────────────────────────────────

@login_required
@require_POST
def generate_units(request, pk):
    pm   = get_object_or_404(ProductModel, pk=pk, manufacturer=request.user)
    form = GenerateUnitsForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid quantity.")
        return redirect("product_model_detail", pk=pk)

    qty        = form.cleaned_data["quantity"]
    base_index = pm.units.count()
    host       = request.get_host()

    for i in range(qty):
        ts     = time.time() + i * 0.001
        serial = generate_unit_serial(pm.model_code, base_index + i + 1)
        p_hash = generate_product_hash(serial, pm.pk, ts)

        unit = ProductUnit.objects.create(
            model=pm, serial_number=serial,
            product_hash=p_hash, current_owner=request.user, status="REGISTERED",
        )
        verify_url = f"http://{host}/verify/{p_hash}/"
        qr_file    = generate_qr(p_hash, verify_url)
        unit.qr_code.save(qr_file.name, qr_file, save=False)

        block = add_block(
            event_type="REGISTERED",
            product_unit_serial=serial,
            actor_username=request.user.username,
            actor_role="MANUFACTURER",
            extra_data={"model_code": pm.model_code, "model_name": pm.name},
        )
        unit.blockchain_block_hash = block.block_hash
        unit.save()

    messages.success(request, f"✅ {qty} unit(s) generated with QR codes and blockchain records.")
    return redirect("product_model_detail", pk=pk)


# ── Unit Detail + Transfer ────────────────────────────────────────────────────

@login_required
def unit_detail(request, serial):
    unit      = get_object_or_404(ProductUnit, serial_number=serial)
    history   = get_unit_history(serial)
    transfers = unit.transfers.all()
    return render(request, "products/unit_detail.html", {
        "unit": unit, "history": history,
        "transfers": transfers, "transfer_form": TransferForm(),
    })


@login_required
@require_POST
def transfer_unit(request, serial):
    unit = get_object_or_404(ProductUnit, serial_number=serial, current_owner=request.user)
    form = TransferForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid transfer data.")
        return redirect("unit_detail", serial=serial)
    try:
        to_user = User.objects.get(username=form.cleaned_data["to_username"])
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("unit_detail", serial=serial)

    old_owner          = unit.current_owner
    unit.current_owner = to_user
    unit.status        = "IN_TRANSIT" if to_user.is_distributor() else "WITH_SELLER"
    unit.save()

    block = add_block(
        event_type="TRANSFERRED",
        product_unit_serial=unit.serial_number,
        actor_username=request.user.username,
        actor_role=request.user.role,
        extra_data={"from": old_owner.username if old_owner else "",
                    "to": to_user.username,
                    "notes": form.cleaned_data.get("notes", "")},
    )
    TransferHistory.objects.create(
        unit=unit, from_user=old_owner, to_user=to_user,
        notes=form.cleaned_data.get("notes", ""),
        block_hash=block.block_hash,
    )
    messages.success(request, f"Unit transferred to {to_user.username}.")
    return redirect("unit_detail", serial=serial)


# ── Verification — public ─────────────────────────────────────────────────────

def verify_unit(request, product_hash):
    result = verify(product_hash)
    unit   = result.get("unit")

    ip  = get_client_ip(request)
    geo = get_location(ip)

    scan = ScanLog.objects.create(
        unit=unit,
        product_hash_scanned=product_hash,
        scanner_ip=ip or None,
        scanner_user=request.user if request.user.is_authenticated else None,
        geo_country=geo.get("country", ""),
        geo_city=geo.get("city", ""),
        geo_lat=geo.get("lat"),
        geo_lon=geo.get("lon"),
        result=result["result"],
    )

    if unit and result["result"] in ("SUSPICIOUS", "FAKE"):
        unit.status = "FLAGGED"
        unit.save(update_fields=["status"])
        alert_suspicious_scan(unit, scan, unit.model.manufacturer)

    return render(request, "products/verify.html", {
        "result":             result,
        "unit":               unit,
        "scan":               scan,
        "blockchain_history": get_unit_history(unit.serial_number) if unit else [],
        "product_hash":       product_hash,
    })


# ── Chain Explorer ────────────────────────────────────────────────────────────

@login_required
def chain_status(request):
    from blockchain.models import BlockRecord
    is_valid, msg = validate_chain()
    blocks        = BlockRecord.objects.order_by("-index")[:50]
    return render(request, "products/chain_status.html",
                  {"is_valid": is_valid, "msg": msg, "blocks": blocks})


# ── AJAX ──────────────────────────────────────────────────────────────────────

@login_required
def api_scan_stats(request):
    since = timezone.now() - timedelta(hours=24)
    qs    = ScanLog.objects.filter(unit__model__manufacturer=request.user)
    return JsonResponse({
        "total":      qs.count(),
        "scans_24h":  qs.filter(scanned_at__gte=since).count(),
        "genuine":    qs.filter(result="GENUINE").count(),
        "suspicious": qs.filter(result="SUSPICIOUS").count(),
        "fake":       qs.filter(result="FAKE").count(),
    })


