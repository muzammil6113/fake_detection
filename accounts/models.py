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
        (ROLE_MANUFACTURER, "Manufacturer"),
        (ROLE_DISTRIBUTOR, "Distributor"),
        (ROLE_CUSTOMER, "Customer"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    company = models.CharField(max_length=200, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")

    def is_manufacturer(self) -> bool:
        return self.role == self.ROLE_MANUFACTURER

    def is_distributor(self) -> bool:
        return self.role == self.ROLE_DISTRIBUTOR

    def __str__(self) -> str:
        return self.username

