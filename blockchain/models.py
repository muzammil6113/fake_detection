from django.db import models


class BlockRecord(models.Model):
    EVENT_CHOICES = [
        ("REGISTERED",  "Product Registered"),
        ("TRANSFERRED", "Transferred in Supply Chain"),
        ("SOLD",        "Sold to Customer"),
        ("FLAGGED",     "Flagged Suspicious"),
    ]

    index               = models.PositiveIntegerField()
    block_hash          = models.CharField(max_length=64, unique=True)
    previous_hash       = models.CharField(max_length=64)
    nonce               = models.PositiveIntegerField(default=0)
    timestamp           = models.FloatField()
    event_type          = models.CharField(max_length=20, choices=EVENT_CHOICES)
    product_unit_serial = models.CharField(max_length=120)
    actor_username      = models.CharField(max_length=150)
    actor_role          = models.CharField(max_length=50)
    extra_data          = models.JSONField(default=dict, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["index"]

    def __str__(self):
        return f"Block #{self.index} | {self.event_type} | {self.product_unit_serial}"