import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


@login_required
def scan_page(request):
    return render(request, 'blockchain/scan.html')


@login_required
def verify_hash(request):
    """
    API endpoint for QR verification. Returns JSON with verification result.
    
    Checks:
    1. Hash exists in DB
    2. Supply chain valid (manufacturer linked)
    3. No duplicate/geo attack within time window
    
    Result codes: GENUINE, SUSPICIOUS, FAKE
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    scanned_hash = data.get('hash', '').strip()

    if not scanned_hash:
        return JsonResponse({'error': 'No hash received'}, status=400)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

    from products.models import ProductUnit
    from blockchain.models import ScanLog

    # ────────────────────────────────────────────────────────────────
    # STEP 1: Fetch the product unit by hash
    # ────────────────────────────────────────────────────────────────
    try:
        unit = ProductUnit.objects.select_related(
            'model', 'model__manufacturer'
        ).get(product_hash=scanned_hash)
    except ProductUnit.DoesNotExist:
        # Hash not found - this is a FAKE product
        try:
            ScanLog.objects.create(
                user=request.user,
                product_unit_serial='UNKNOWN',
                product_name='Unknown',
                result='INVALID',
                scanned_from_ip=ip,
                extra_data={'scanned_hash': scanned_hash}
            )
        except Exception as log_err:
            # Log creation failed, but still return the response
            pass

        return JsonResponse({
            'result': 'FAKE',
            'message': 'This product is NOT in our blockchain ledger.',
            'color': 'red',
        }, status=200)

    except Exception as e:
        # Database or other critical error
        return JsonResponse({
            'result': 'ERROR',
            'message': f'Server error: {str(e)}',
            'color': 'red',
        }, status=500)

    # ────────────────────────────────────────────────────────────────
    # STEP 2: Verify supply chain validity
    # ────────────────────────────────────────────────────────────────
    if not unit.model or not unit.model.manufacturer_id:
        result = 'SUSPICIOUS'
        message = 'No valid manufacturer linked to this product.'
        color = 'amber'
    else:
        # ────────────────────────────────────────────────────────────
        # STEP 3: Check for duplicate/cloning attacks
        # ────────────────────────────────────────────────────────────
        threshold = int(getattr(settings, 'SUSPICIOUS_SCAN_COUNT', 3))
        window_minutes = int(getattr(settings, 'SUSPICIOUS_SCAN_WINDOW_MINUTES', 60))
        window = timezone.now() - timedelta(minutes=window_minutes)

        scan_count = ScanLog.objects.filter(
            product_unit_serial=unit.serial_number,
            scanned_at__gte=window
        ).count()

        if scan_count >= threshold:
            result = 'SUSPICIOUS'
            message = (
                f'⚠️ Cloning detected: Scanned {scan_count + 1}× '
                f'in the last {window_minutes} min — exceeds threshold.'
            )
            color = 'amber'
        else:
            # All checks passed!
            result = 'GENUINE'
            manufacturer = unit.model.manufacturer
            manufacturer_display = (
                manufacturer.company_name.strip() or manufacturer.username
            ) if manufacturer else 'Unknown'
            message = f'✓ Genuine product. Manufactured by {manufacturer_display}.'
            color = 'green'

    # ────────────────────────────────────────────────────────────────
    # Log the scan result
    # ────────────────────────────────────────────────────────────────
    manufacturer_name = unit.model.manufacturer.username if unit.model and unit.model.manufacturer else 'Unknown'
    if unit.model and unit.model.manufacturer and unit.model.manufacturer.company_name:
        manufacturer_name = unit.model.manufacturer.company_name

    # ── Log the scan ─────────────────────────────────────────────────────────
    scan_log = None
    try:
        scan_log = ScanLog.objects.create(
            user=request.user,
            product_unit_serial=unit.serial_number,
            product_name=unit.model.name if unit.model else 'Unknown',
            result=result if result in ['GENUINE', 'SUSPICIOUS', 'FAKE'] else 'INVALID',
            scanned_from_ip=ip,
            extra_data={
                'scanned_hash': scanned_hash,
                'manufacturer': manufacturer_name,
            }
        )
    except Exception as log_err:
        pass

    # ── Alert manufacturer on suspicious scans ────────────────────────────────
    if result == 'SUSPICIOUS' and unit.model and unit.model.manufacturer:
        try:
            from products.alert_utils import alert_suspicious_scan
            from products.models import ScanLog as ProductScanLog

            # Build a lightweight scan object for the alert
            # (uses products.ScanLog structure that alert_utils expects)
            class _ScanProxy:
                def __init__(self, ip, city, country, r, ts):
                    self.scanner_ip  = ip
                    self.geo_city    = city
                    self.geo_country = country
                    self.result      = r
                    self.scanned_at  = ts

            
            proxy_scan = _ScanProxy(
                ip=ip,
                city='',
                country='',
                r=result,
                ts=timezone.now(),
            )
            alert_suspicious_scan(unit, proxy_scan, unit.model.manufacturer)
        except Exception as alert_err:
            # Never block the response because of an alert failure
            pass

    return JsonResponse({
        'result': result,
        'message': message,
        'color': color,
        'product_name': unit.model.name if unit.model else 'Unknown',
        'serial': unit.serial_number,
        'manufacturer': manufacturer_name,
    }, status=200)