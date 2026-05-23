"""
3-check waterfall:
  1. Hash in DB?            No  → FAKE
  2. Supply chain valid?    No  → SUSPICIOUS
  3. Duplicate/geo attack?  Yes → SUSPICIOUS
  All pass                      → GENUINE
"""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import ProductUnit, ScanLog


def _check_hash(h):
    try:
        return ProductUnit.objects.get(product_hash=h), None
    except ProductUnit.DoesNotExist:
        return None, "Hash not found in blockchain registry. This QR is NOT registered."


def _check_supply_chain(unit):
    if not unit.model.manufacturer_id:
        return False, "No manufacturer linked to this product."
    return True, ""


def _check_duplicate(unit):
    window = settings.SUSPICIOUS_SCAN_WINDOW_MINUTES
    thresh = settings.SUSPICIOUS_SCAN_COUNT
    since  = timezone.now() - timedelta(minutes=window)
    count  = ScanLog.objects.filter(unit=unit, scanned_at__gte=since).count()
    if count >= thresh:
        countries = set(
            ScanLog.objects.filter(unit=unit, scanned_at__gte=since)
            .exclude(geo_country="").values_list("geo_country", flat=True)
        )
        if len(countries) > 2:
            return True, (f"QR scanned from {len(countries)} countries in {window} min — "
                          f"cloning attack suspected.")
        return True, (f"QR scanned {count} times in {window} min — "
                      f"exceeds threshold of {thresh}.")
    return False, ""


def verify(product_hash: str) -> dict:
    checks = {}

    unit, err = _check_hash(product_hash)
    checks["hash_valid"] = unit is not None
    if not unit:
        return {"result": "FAKE", "unit": None, "message": err,
                "checks": checks, "color": "red", "icon": "✗"}

    ok, msg = _check_supply_chain(unit)
    checks["supply_chain_valid"] = ok
    if not ok:
        return {"result": "SUSPICIOUS", "unit": unit, "message": msg,
                "checks": checks, "color": "amber", "icon": "⚠"}

    dup, msg = _check_duplicate(unit)
    checks["no_duplicate"] = not dup
    if dup:
        return {"result": "SUSPICIOUS", "unit": unit, "message": msg,
                "checks": checks, "color": "amber", "icon": "⚠"}

    return {"result": "GENUINE", "unit": unit,
            "message": "All 3 verification checks passed. This is an authentic product.",
            "checks": checks, "color": "green", "icon": "✓"}