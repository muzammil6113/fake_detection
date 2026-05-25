from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model used by BlockVerify.

    Roles:
      - MANUFACTURER: registers product models + generates units
      - DISTRIBUTOR: transfers units along the supply chain
      - CUSTOMER: scans QR codes and verifies authenticity
    """

    ROLE_MANUFACTURER = "MANUFACTURER"
    ROLE_DISTRIBUTOR = "DISTRIBUTOR"
    ROLE_CUSTOMER = "CUSTOMER"

    ROLE_CHOICES = [
        ('MANUFACTURER', 'Manufacturer'),
        ('DISTRIBUTOR', 'Distributor'),
        ('CUSTOMER', 'Customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    company_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    def is_manufacturer(self) -> bool:
        return self.role == self.ROLE_MANUFACTURER

    def is_distributor(self) -> bool:
        return self.role == self.ROLE_DISTRIBUTOR

    def __str__(self) -> str:
        return self.username

