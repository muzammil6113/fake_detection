import requests
from django.conf import settings


def get_client_ip(request) -> str:
    x = request.META.get("HTTP_X_FORWARDED_FOR")
    return x.split(",")[0].strip() if x else request.META.get("REMOTE_ADDR", "")


import ipaddress

def get_location(ip: str) -> dict:
    """Returns {country, city, lat, lon}. Empty dict on failure."""
    if not ip:
        return {}
    
    # ── Handle private/local IPs ─────────────────────────────────
    if ip in ("127.0.0.1", "::1", "localhost"):
        return {"country": "Local", "city": "Localhost", "lat": None, "lon": None}
    
    try:
        parsed = ipaddress.ip_address(ip)
        if parsed.is_private or parsed.is_loopback or parsed.is_link_local:
            return {"country": "Local Network", "city": f"Private IP ({ip})", "lat": None, "lon": None}
    except ValueError:
        pass  # not a valid IP, proceed anyway

    try:
        params = {"token": settings.IPINFO_TOKEN} if settings.IPINFO_TOKEN else {}
        r = requests.get(f"https://ipinfo.io/{ip}/json", params=params, timeout=3)
        if r.status_code == 200:
            d   = r.json()
            loc = d.get("loc", "").split(",")
            return {
                "country": d.get("country", ""),
                "city":    d.get("city", ""),
                "lat":     float(loc[0]) if len(loc) == 2 else None,
                "lon":     float(loc[1]) if len(loc) == 2 else None,
            }
    except Exception:
        pass
    return {}