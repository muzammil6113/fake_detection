"""
3-check waterfall for QR verification:

  1. Hash in DB?                  No  → FAKE
  2. Supply chain valid?          No  → SUSPICIOUS
  3. Duplicate/geo attack?        Yes → SUSPICIOUS
  All pass                            → GENUINE
"""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import ProductUnit, ScanLog


def _check_hash(h):
    """Check 1: Does the QR hash exist in our registry?"""
    try:
        unit = ProductUnit.objects.select_related('model', 'model__manufacturer').get(
            product_hash=h
        )
        return unit, None
    except ProductUnit.DoesNotExist:
        return None, "Hash not found in blockchain registry. This QR is NOT registered."
    except Exception as e:
        return None, f"Database error checking hash: {str(e)}"


def _check_supply_chain(unit):
    """Check 2: Is the product's supply chain valid?"""
    if not unit:
        return False, "No product unit found."
    
    if not unit.model:
        return False, "Product has no model reference."
    
    if not unit.model.manufacturer_id:
        return False, "No manufacturer linked to this product model."
    
    # Check if product unit status is valid (not flagged)
    if unit.status == "FLAGGED":
        return False, "This product has been flagged as suspicious."
    
    return True, ""


def _check_duplicate(unit):
    """
    Check 3: Is this a duplicate/cloning attack?
    
    Detects multiple rapid scans from different locations/devices.
    """
    if not unit:
        return False, ""
    
    try:
        window = settings.SUSPICIOUS_SCAN_WINDOW_MINUTES
        thresh = settings.SUSPICIOUS_SCAN_COUNT
    except AttributeError:
        window = 60
        thresh = 3
    
    since = timezone.now() - timedelta(minutes=window)
    
    try:
        scans = ScanLog.objects.filter(
            unit=unit,
            scanned_at__gte=since
        ).order_by('scanned_at')
        
        count = scans.count()
        
        if count >= thresh:
            # Multiple scans detected - check for geo attacks
            countries = set(
                scans.exclude(geo_country="").values_list("geo_country", flat=True)
            )
            ips = set(
                scans.exclude(scanner_ip__isnull=True).values_list("scanner_ip", flat=True)
            )
            
            if len(countries) > 2:
                return True, (
                    f"Cloning attack detected: QR scanned from {len(countries)} "
                    f"different countries in {window} minutes."
                )
            
            if len(ips) > 2:
                return True, (
                    f"Cloning attack detected: QR scanned from {len(ips)} "
                    f"different devices in {window} minutes."
                )
            
            return True, (
                f"Suspicious activity detected: QR scanned {count} times in {window} min "
                f"(threshold: {thresh}). Possible counterfeit or clone."
            )
        
        return False, ""
    
    except Exception as e:
        # If we can't check duplicates, consider it suspicious to be safe
        return True, f"Could not verify duplicate scans: {str(e)}"


def verify(product_hash: str) -> dict:
    """
    Main verification function. Performs 3-check waterfall.
    
    Returns:
        dict with keys:
            - result: "GENUINE", "SUSPICIOUS", or "FAKE"
            - unit: ProductUnit object or None
            - message: Human-readable result message
            - color: "green", "amber", or "red"
            - icon: "✓", "⚠", or "✗"
            - checks: dict of individual check results
    """
    checks = {}

    # ──────────────────────────────────────────────────────────────
    # CHECK 1: Hash valid?
    # ──────────────────────────────────────────────────────────────
    unit, err = _check_hash(product_hash)
    checks["hash_valid"] = unit is not None
    
    if not unit:
        return {
            "result": "FAKE",
            "unit": None,
            "message": err or "QR code is not registered in our system.",
            "checks": checks,
            "color": "red",
            "icon": "✗",
        }

    # ──────────────────────────────────────────────────────────────
    # CHECK 2: Supply chain valid?
    # ──────────────────────────────────────────────────────────────
    ok, msg = _check_supply_chain(unit)
    checks["supply_chain_valid"] = ok
    
    if not ok:
        return {
            "result": "SUSPICIOUS",
            "unit": unit,
            "message": msg or "Product supply chain validation failed.",
            "checks": checks,
            "color": "amber",
            "icon": "⚠",
        }

    # ──────────────────────────────────────────────────────────────
    # CHECK 3: No duplicate/cloning attack?
    # ──────────────────────────────────────────────────────────────
    dup, msg = _check_duplicate(unit)
    checks["no_duplicate"] = not dup
    
    if dup:
        return {
            "result": "SUSPICIOUS",
            "unit": unit,
            "message": msg or "Duplicate scan detected.",
            "checks": checks,
            "color": "amber",
            "icon": "⚠",
        }

    # ──────────────────────────────────────────────────────────────
    # ALL CHECKS PASSED → GENUINE
    # ──────────────────────────────────────────────────────────────
    manufacturer_name = (
        (unit.model.manufacturer.company_name.strip() 
         if unit.model.manufacturer.company_name else None)
        or unit.model.manufacturer.username
    ) if unit.model and unit.model.manufacturer else "Unknown"
    
    return {
        "result": "GENUINE",
        "unit": unit,
        "message": (
            f"✓ All verification checks passed. "
            f"This is an authentic {unit.model.name if unit.model else 'product'} "
            f"by {manufacturer_name}."
        ),
        "checks": checks,
        "color": "green",
        "icon": "✓",
    }