from django.conf import settings
from django.db import models


class BlockRecord(models.Model):
    EVENT_CHOICES = [
        ("REGISTERED",  "Product Registered"),
        ("TRANSFERRED", "Transferred in Supply Chain"),
        ("SOLD",        "Sold to Customer"),
        ("FLAGGED",     "Flagged Suspicious"),
    ]

    index = models.PositiveIntegerField()
    block_hash = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64)
    nonce = models.PositiveIntegerField(default=0)
    timestamp = models.FloatField()
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    product_unit_serial = models.CharField(max_length=120)
    actor_username = models.CharField(max_length=150)
    actor_role = models.CharField(max_length=50)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["index"]

    def __str__(self):
        return f"Block #{self.index} | {self.event_type} | {self.product_unit_serial}"


class ScanLog(models.Model):
    """Stores a customer's QR/product scan result."""

    RESULT_CHOICES = [
        ("VALID", "Valid"),
        ("INVALID", "Invalid"),
        ("SUSPICIOUS", "Suspicious"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scan_logs",
    )

    # QR / product identifiers
    product_unit_serial = models.CharField(max_length=120, db_index=True)

    # Optional snapshot of product data shown in UI
    # (filled when available by scan/verify flow)
    product_name = models.CharField(max_length=255, blank=True, default="")

    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="INVALID")

    # Time used by customer_home template
    scanned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Extra project requirements: keep device/location metadata if your scan flow provides it
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    scanned_from_ip = models.GenericIPAddressField(null=True, blank=True)

    # Keep raw payload / notes (useful for debugging & audits)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"ScanLog({self.user}, {self.product_unit_serial}, {self.result})"
