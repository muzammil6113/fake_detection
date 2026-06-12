import time
from datetime import timedelta
from products.models import ProductModel, ProductUnit, TransferHistory, ProductRequest
# from blockchain.utils import add_block   # adjust path to match your project
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import ProductModel, ProductUnit, ScanLog, TransferHistory, Category, ProductRequest
from .forms import ProductModelForm, GenerateUnitsForm, TransferForm
from .qr_utils import generate_qr
from .geo_utils import get_client_ip, get_location
from .verification import verify
from .alert_utils import alert_suspicious_scan
from blockchain.engine import generate_product_hash, generate_unit_serial
from blockchain.service import add_block, validate_chain, get_unit_history
from accounts.models import User
from blockchain.models import ScanLog


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
    ctx = {"user": user}

    if user.is_manufacturer():

        ctx["models"] = ProductModel.objects.filter(
            manufacturer=user
        ).order_by("-created_at")

        ctx["units"] = ProductUnit.objects.filter(
            model__manufacturer=user
        ).order_by("-updated_at")[:20]

        ctx["total_units"] = ProductUnit.objects.filter(
            model__manufacturer=user
        ).count()

        ctx["flagged"] = ProductUnit.objects.filter(
            model__manufacturer=user,
            status="FLAGGED"
        ).count()

        ctx["pending_requests"] = ProductRequest.objects.filter(
        manufacturer=user, status='pending'
        ).count()

        serials = ProductUnit.objects.filter(
            model__manufacturer=user
        ).values_list(
            "serial_number",
            flat=True
        )

        ctx["recent_scans"] = ScanLog.objects.filter(
            product_unit_serial__in=serials
        ).order_by("-scanned_at")[:20]


        
        return render(request, "dashboard.html", ctx)

    elif user.is_distributor():

        units = ProductUnit.objects.filter(
            current_owner=user
        ).order_by("-updated_at")

        return render(
            request,
            "accounts/distributor_home.html",
            {
                "units": units
            }
        )

    else:

        scans = ScanLog.objects.filter(
            user=user
        ).order_by("-scanned_at")[:20]

        return render(
            request,
            "accounts/customer_home.html",
            {
                "scans": scans
            }
        )

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

    if request.user.role != 'manufacturer':
        messages.error(request, "Only manufacturers can transfer products.")
        return redirect("products:dashboard")

    unit = get_object_or_404(ProductUnit, serial_number=serial, current_owner=request.user)
    form = TransferForm(request.POST)

    if not form.is_valid():
        messages.error(request, "Invalid transfer data.")
        return redirect("products:unit_detail", serial=serial)

    try:
        to_user = User.objects.get(username=form.cleaned_data["to_username"])
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("products:unit_detail", serial=serial)

    old_owner = unit.current_owner
    unit.current_owner = to_user
    unit.status = "IN_TRANSIT" if to_user.is_distributor() else "WITH_SELLER"
    unit.save()

    block = add_block(
        event_type="TRANSFERRED",
        product_unit_serial=unit.serial_number,
        actor_username=request.user.username,
        actor_role=request.user.role,
        extra_data={
            "from": old_owner.username if old_owner else "",
            "to": to_user.username,
            "notes": form.cleaned_data.get("notes", ""),
        },
    )

    TransferHistory.objects.create(
        unit=unit,
        from_user=old_owner,
        to_user=to_user,
        notes=form.cleaned_data.get("notes", ""),
        block_hash=block.block_hash,
    )

    messages.success(request, f"Unit transferred to {to_user.username}.")
    return redirect("products:unit_detail", serial=serial)


# ── Verification — public ─────────────────────────────────────────────────────

def verify_unit(request, product_hash):
    """
    Public QR verification endpoint. Uses 3-check verification logic:
    1. Hash exists in registry
    2. Supply chain valid
    3. No duplicate/cloning attack
    
    Returns GENUINE / SUSPICIOUS / FAKE result and logs the scan.
    """
    try:
        result = verify(product_hash)
        unit = result.get("unit")
    except Exception as e:
        # Verification failed - return error
        return render(request, "products/verify.html", {
            "result": {
                "result": "ERROR",
                "message": f"Verification failed: {str(e)}",
                "color": "red",
                "icon": "✗",
                "checks": {},
            },
            "unit": None,
            "scan": None,
            "blockchain_history": [],
            "product_hash": product_hash,
        })

    ip = get_client_ip(request)
    geo = get_location(ip)

    # Log the scan attempt
    scan = None
    try:
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
    except Exception as log_err:
        # Log creation failed, but don't fail the verification response
        pass

    # Flag suspicious/fake products
    try:
        if unit and result["result"] in ("SUSPICIOUS", "FAKE"):
            unit.status = "FLAGGED"
            unit.save(update_fields=["status"])
            if unit.model and unit.model.manufacturer:
                alert_suspicious_scan(unit, scan, unit.model.manufacturer)
    except Exception as flag_err:
        # Flag/alert failed, but don't fail the response
        pass

    return render(request, "products/verify.html", {
        "result": result,
        "unit": unit,
        "scan": scan,
        "blockchain_history": get_unit_history(unit.serial_number) if unit else [],
        "product_hash": product_hash,
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




@login_required
def accept_request(request, req_id):
    req = get_object_or_404(ProductRequest, pk=req_id, manufacturer=request.user)

    if req.status != 'pending':
        messages.warning(request, "Request already handled.")
        return redirect('products:request_inbox')

    # Get available units owned by this manufacturer for the requested product
    available_units = ProductUnit.objects.filter(
    model=req.product,          # ← model, not product
    current_owner=request.user
)

    if available_units.count() < req.quantity:
        messages.error(
            request,
            f"Not enough units. You have {available_units.count()}, requested {req.quantity}."
        )
        return redirect('products:request_inbox')

    # Bulk transfer — reuse exact same logic as transfer_unit
    units_to_transfer = available_units[:req.quantity]

    for unit in units_to_transfer:
        old_owner = unit.current_owner
        unit.current_owner = req.distributor
        unit.status = "IN_TRANSIT"
        unit.save()

        block = add_block(
            event_type="TRANSFERRED",
            product_unit_serial=unit.serial_number,
            actor_username=request.user.username,
            actor_role=request.user.role,
            extra_data={
                "from": old_owner.username if old_owner else "",
                "to": req.distributor.username,
                "notes": f"Bulk transfer via request #{req.pk}",
            },
        )

        TransferHistory.objects.create(
            unit=unit,
            from_user=old_owner,
            to_user=req.distributor,
            notes=f"Bulk transfer via request #{req.pk}",
            block_hash=block.block_hash,
        )

    req.status = 'accepted'
    req.save()

    messages.success(
        request,
        f"Transferred {req.quantity}x {req.product.name} to {req.distributor.username}."
    )
    return redirect('products:request_inbox')




# ── Distributor: browse manufacturers ────────────────────────────────────────

@login_required
def manufacturer_list(request):
    if not request.user.is_distributor():
        messages.error(request, "Only distributors can browse manufacturers.")
        return redirect("products:dashboard")
    manufacturers = User.objects.filter(role='MANUFACTURER')
    return render(request, "products/manufacturer_list.html", {
        "manufacturers": manufacturers
    })


@login_required
def manufacturer_products(request, mfr_id):
    if not request.user.is_distributor():
        messages.error(request, "Only distributors can browse manufacturer products.")
        return redirect("products:dashboard")
    manufacturer = get_object_or_404(User, pk=mfr_id, role='MANUFACTURER')
    products = ProductModel.objects.filter(manufacturer=manufacturer)

    # Annotate each product with count of units still owned by manufacturer
    from django.db.models import Count, Q
    products = products.annotate(
        available_count=Count(
            'units',
            filter=Q(units__current_owner=manufacturer)
        )
    )

    return render(request, "products/manufacturer_products.html", {
        "manufacturer": manufacturer,
        "products": products,
    })


@login_required
@require_POST
def request_product(request, mfr_id, product_id):
    if not request.user.is_distributor():
        messages.error(request, "Only distributors can request products.")
        return redirect("products:dashboard")
    product = get_object_or_404(ProductModel, pk=product_id, manufacturer__pk=mfr_id)
    quantity = int(request.POST.get("quantity", 0))
    note = request.POST.get("note", "")
    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect("products:manufacturer_products", mfr_id=mfr_id)
    ProductRequest.objects.create(
        distributor=request.user,
        manufacturer=product.manufacturer,
        product=product,
        quantity=quantity,
        note=note,
    )
    messages.success(request, f"Request sent to {product.manufacturer.username}.")
    return redirect("products:manufacturer_list")


# ── Manufacturer: request inbox ───────────────────────────────────────────────

@login_required
def request_inbox(request):
    if not request.user.is_manufacturer():
        messages.error(request, "Only manufacturers can view the inbox.")
        return redirect("products:dashboard")
    requests_qs = ProductRequest.objects.filter(
        manufacturer=request.user,
        status='pending'
    ).select_related('distributor', 'product').order_by('-created_at')
    return render(request, "products/request_inbox.html", {
        "requests": requests_qs
    })


@login_required
@require_POST
def deny_request(request, req_id):
    req = get_object_or_404(ProductRequest, pk=req_id, manufacturer=request.user)
    req.status = 'denied'
    req.save()
    messages.info(request, "Request denied.")
    return redirect('products:request_inbox')



@login_required
def my_requests(request):
    if not request.user.is_distributor():
        return redirect("products:dashboard")
    reqs = ProductRequest.objects.filter(
        distributor=request.user
    ).select_related('product', 'manufacturer').order_by('-created_at')
    return render(request, "products/my_requests.html", {"requests": reqs})





@login_required
def distributor_home(request):
    if not request.user.is_distributor():
        return redirect("products:dashboard")
    units = ProductUnit.objects.filter(
        current_owner=request.user
    ).order_by("-updated_at")
    return render(request, "accounts/distributor_home.html", {
        "units": units
    })