"""python manage.py seed_demo  — creates demo users + product + 5 units"""
import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed BlockVerify with demo data"

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from products.models import ProductModel, ProductUnit, Category, TransferHistory
        from products.qr_utils import generate_qr
        from blockchain.engine import generate_product_hash, generate_unit_serial
        from blockchain.service import add_block

        User = get_user_model()
        self.stdout.write(self.style.SUCCESS("🌱 Seeding..."))

        # Users
        mfr, _ = User.objects.get_or_create(username="nike_mfr", defaults={
            "email": "mfr@demo.com", "role": "MANUFACTURER",
            "company": "Nike Inc.", "first_name": "Nike", "last_name": "Manufacturer",
            "phone": "+1234567890",
        })
        mfr.set_password("demo1234"); mfr.save()

        dist, _ = User.objects.get_or_create(username="dist_john", defaults={
            "email": "dist@demo.com", "role": "DISTRIBUTOR",
            "company": "John Sports", "first_name": "John", "last_name": "Distributor",
        })
        dist.set_password("demo1234"); dist.save()

        cust, _ = User.objects.get_or_create(username="customer_ali", defaults={
            "email": "cust@demo.com", "role": "CUSTOMER",
            "first_name": "Ali", "last_name": "Customer",
        })
        cust.set_password("demo1234"); cust.save()
        self.stdout.write("  ✅ 3 users (password: demo1234)")

        # Category + model
        cat, _ = Category.objects.get_or_create(name="Footwear")
        pm, created = ProductModel.objects.get_or_create(model_code="NIKEAF1", defaults={
            "manufacturer": mfr, "name": "Air Force 1 White",
            "brand": "Nike", "category": cat,
            "description": "Classic Nike Air Force 1 all-white leather.",
        })
        self.stdout.write(f"  {'✅ Created' if created else 'ℹ️  Exists'}: Nike Air Force 1 White")

        # Units
        if pm.units.count() == 0:
            created_units = []
            for i in range(5):
                ts     = time.time() + i * 0.01
                serial = generate_unit_serial(pm.model_code, i + 1)
                p_hash = generate_product_hash(serial, pm.pk, ts)
                unit   = ProductUnit.objects.create(
                    model=pm, serial_number=serial, product_hash=p_hash,
                    current_owner=mfr, status="REGISTERED",
                )
                qr = generate_qr(p_hash, f"http://127.0.0.1:8000/verify/{p_hash}/")
                unit.qr_code.save(qr.name, qr, save=False)
                block = add_block("REGISTERED", serial, mfr.username, "MANUFACTURER",
                                  {"model_code": pm.model_code})
                unit.blockchain_block_hash = block.block_hash
                unit.save()
                created_units.append(unit)
            self.stdout.write("  ✅ 5 units with QR + blockchain records")

            # Transfer unit 1 to distributor
            u1 = created_units[0]
            old = u1.current_owner
            u1.current_owner = dist; u1.status = "IN_TRANSIT"
            block = add_block("TRANSFERRED", u1.serial_number, mfr.username, "MANUFACTURER",
                              {"from": mfr.username, "to": dist.username})
            TransferHistory.objects.create(unit=u1, from_user=old, to_user=dist,
                                           notes="Initial distribution", block_hash=block.block_hash)
            u1.save()
            self.stdout.write("  ✅ Unit #1 transferred to distributor")
        else:
            self.stdout.write("  ℹ️  Units already exist")

        self.stdout.write("\n" + "━" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Done!\n"))
        self.stdout.write("  Credentials (password: demo1234):")
        self.stdout.write("    Manufacturer  → nike_mfr")
        self.stdout.write("    Distributor   → dist_john")
        self.stdout.write("    Customer      → customer_ali\n")
        self.stdout.write("  Test verify URLs:")
        for u in pm.units.all()[:3]:
            self.stdout.write(f"    http://127.0.0.1:8000/verify/{u.product_hash}/")
        self.stdout.write("━" * 60)