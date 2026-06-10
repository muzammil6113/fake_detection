from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name


class ProductModel(models.Model):
    """Product line — e.g. 'Nike Air Force 1'. One model → many physical units."""
    manufacturer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     on_delete=models.CASCADE, related_name="product_models")
    name         = models.CharField(max_length=200)
    brand        = models.CharField(max_length=100)
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    model_code   = models.CharField(max_length=30, unique=True,
                                    help_text="Short unique code e.g. NIKEAF1")
    description  = models.TextField(blank=True)
    image        = models.ImageField(upload_to="product_images/", blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.brand} — {self.name} ({self.model_code})"
    def unit_count(self): return self.units.count()


class ProductUnit(models.Model):
    """One physical item. Unique serial + SHA-256 hash + QR + blockchain block."""
    STATUS_CHOICES = [
        ("REGISTERED",  "Registered"),
        ("IN_TRANSIT",  "In Transit"),
        ("WITH_SELLER", "With Seller"),
        ("SOLD",        "Sold"),
        ("FLAGGED",     "Flagged Suspicious"),
    ]
    model                 = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name="units")
    serial_number         = models.CharField(max_length=120, unique=True)
    product_hash          = models.CharField(max_length=64, unique=True)
    qr_code               = models.ImageField(upload_to="qrcodes/", blank=True, null=True)
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default="REGISTERED")
    current_owner         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                              null=True, blank=True, related_name="owned_units")
    blockchain_block_hash = models.CharField(max_length=64, blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.serial_number} [{self.status}]"


class TransferHistory(models.Model):
    """Every custody handoff in supply chain."""
    unit           = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, related_name="transfers")
    from_user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, related_name="transfers_sent")
    to_user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, related_name="transfers_received")
    notes          = models.TextField(blank=True)
    block_hash     = models.CharField(max_length=64, blank=True)
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ["-transferred_at"]
    def __str__(self): return f"{self.unit.serial_number}: {self.from_user} → {self.to_user}"


class ScanLog(models.Model):
    """Every QR verification scan logged for duplicate/clone detection."""
    RESULT_CHOICES = [
        ("GENUINE",    "Genuine"),
        ("SUSPICIOUS", "Suspicious"),
        ("FAKE",       "Fake"),
    ]
    unit                 = models.ForeignKey(ProductUnit, on_delete=models.CASCADE,
                                             related_name="scans", null=True, blank=True)
    product_hash_scanned = models.CharField(max_length=64)
    scanner_ip           = models.GenericIPAddressField(null=True, blank=True)
    scanner_user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name="scans_made")
    geo_country          = models.CharField(max_length=100, blank=True)
    geo_city             = models.CharField(max_length=100, blank=True)
    geo_lat              = models.FloatField(null=True, blank=True)
    geo_lon              = models.FloatField(null=True, blank=True)
    result               = models.CharField(max_length=20, choices=RESULT_CHOICES)
    scanned_at           = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ["-scanned_at"]
    def __str__(self): return f"{self.product_hash_scanned[:12]}… → {self.result}"




User = get_user_model()

class ProductRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    ]

    distributor = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sent_requests'
    )
    manufacturer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='received_requests'
    )
    product = models.ForeignKey(
        'ProductModel',          # ← fixed
        on_delete=models.CASCADE,
        related_name='requests'
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.distributor} → {self.product} x{self.quantity} [{self.status}]"
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    ]

    distributor = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sent_requests'
    )
    manufacturer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='received_requests'
    )
    product = models.ForeignKey('ProductModel', on_delete=models.CASCADE, related_name='requests')

    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.distributor} → {self.product} x{self.quantity} [{self.status}]"