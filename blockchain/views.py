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

    try:
        unit = ProductUnit.objects.select_related(
            'product', 'product__manufacturer'
        ).get(product_hash=scanned_hash)

    except ProductUnit.DoesNotExist:
        ScanLog.objects.create(
            user=request.user,
            product_unit_serial='UNKNOWN',
            product_name='Unknown',
            result='INVALID',
            scanned_from_ip=ip,
            extra_data={'scanned_hash': scanned_hash}
        )
        return JsonResponse({
            'result':  'FAKE',
            'message': 'This product is NOT in our blockchain ledger.',
            'color':   'red',
        })

    except Exception as e:
        return JsonResponse({'result': 'ERROR', 'message': str(e), 'color': 'red'})

    threshold  = int(getattr(settings, 'SUSPICIOUS_SCAN_COUNT', 3))
    window     = timezone.now() - timedelta(
        minutes=int(getattr(settings, 'SUSPICIOUS_SCAN_WINDOW_MINUTES', 60))
    )
    scan_count = ScanLog.objects.filter(
        product_unit_serial=unit.serial_number,
        scanned_at__gte=window
    ).count()

    if scan_count >= threshold:
        result  = 'SUSPICIOUS'
        message = f'Scanned {scan_count + 1}× in the last hour — possible clone detected.'
        color   = 'amber'
    else:
        result  = 'VALID'
        message = f'Genuine product. Manufactured by {unit.product.manufacturer.company_name or unit.product.manufacturer.username}.'
        color   = 'green'

    manufacturer_name = (
        unit.product.manufacturer.company_name
        or unit.product.manufacturer.username
    )

    ScanLog.objects.create(
        user=request.user,
        product_unit_serial=unit.serial_number,
        product_name=unit.product.name,
        result=result,
        scanned_from_ip=ip,
        extra_data={'scanned_hash': scanned_hash, 'manufacturer': manufacturer_name}
    )

    return JsonResponse({
        'result':       result,
        'message':      message,
        'color':        color,
        'product_name': unit.product.name,
        'serial':       unit.serial_number,
        'manufacturer': manufacturer_name,
    })
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    data         = json.loads(request.body)
    scanned_hash = data.get('hash', '').strip()

    if not scanned_hash:
        return JsonResponse({'error': 'No hash received'}, status=400)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

    from products.models import ProductUnit
    from blockchain.models import ScanLog

    try:
        unit = ProductUnit.objects.select_related(
            'product', 'product__manufacturer'
        ).get(product_hash=scanned_hash)

    except ProductUnit.DoesNotExist:
        ScanLog.objects.create(
            user=request.user,
            product_unit_serial='UNKNOWN',
            product_name='Unknown',
            result='INVALID',
            scanned_from_ip=ip,
            extra_data={'scanned_hash': scanned_hash}
        )
        return JsonResponse({
            'result':  'FAKE',
            'message': 'This product is NOT in our blockchain ledger.',
            'color':   'red',
        })

    threshold  = int(getattr(settings, 'SUSPICIOUS_SCAN_COUNT', 3))
    window     = timezone.now() - timedelta(
        minutes=int(getattr(settings, 'SUSPICIOUS_SCAN_WINDOW_MINUTES', 60))
    )
    scan_count = ScanLog.objects.filter(
        product_unit_serial=unit.serial_number,
        scanned_at__gte=window
    ).count()

    if scan_count >= threshold:
        result  = 'SUSPICIOUS'
        message = f'Scanned {scan_count + 1}× in the last hour — possible clone detected.'
        color   = 'amber'
    else:
        result  = 'VALID'
        message = f'Genuine product. Manufactured by {unit.product.manufacturer.company_name or unit.product.manufacturer.username}.'
        color   = 'green'

    manufacturer_name = (
        unit.product.manufacturer.company_name
        or unit.product.manufacturer.username
    )

    ScanLog.objects.create(
        user=request.user,
        product_unit_serial=unit.serial_number,
        product_name=unit.product.name,
        result=result,
        scanned_from_ip=ip,
        extra_data={'scanned_hash': scanned_hash, 'manufacturer': manufacturer_name}
    )

    return JsonResponse({
        'result':       result,
        'message':      message,
        'color':        color,
        'product_name': unit.product.name,
        'serial':       unit.serial_number,
        'manufacturer': manufacturer_name,
    })