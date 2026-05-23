# BlockVerify — Blockchain-Based Counterfeit Product Detection (QR + SHA-256)

## What this project does
- Manufacturers register product models (Django web app)
- Each physical unit gets:
  - a unique serial number
  - a SHA-256 product hash
  - a QR code that encodes the verify URL
- A blockchain-like immutable ledger stores product events (Django models + PoW hashing)
- Customers scan QR code to verify authenticity:
  - **GENUINE / SUSPICIOUS / FAKE**
  - logs each scan and performs **duplicate/clone detection**
- Supply chain transfers are recorded immutably

## Tech stack
- Django 4.2
- SQLite (default)
- QR generation via `qrcode`
- SHA-256 hashing via Python `hashlib`

## Setup
1. Create/activate your virtual environment (if not already):
   - (Optional) `python -m venv venv`
   - Activate `venv`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. (Optional) Configure environment variables via `.env`:
   - `SENDGRID_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
   - `IPINFO_TOKEN`
   - `SUSPICIOUS_SCAN_COUNT`, `SUSPICIOUS_SCAN_WINDOW_MINUTES`

## Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Seed demo data
```bash
python manage.py seed_demo
```
This creates demo users and sample product/unit records, and prints verify URLs.

## Start the server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open:
- Home: `http://127.0.0.1:8000/`
- Register/Login: `http://127.0.0.1:8000/accounts/register/`

## Demo verify
Use the test verify URLs printed by `seed_demo`:
- `http://127.0.0.1:8000/verify/<product_hash>/`

## Admin
Django admin is available at:
- `http://127.0.0.1:8000/admin/`

