# BlockVerify Advanced Project — TODO

## Phase 1: Make Django app fully working
- [ ] Implement missing `accounts/models.py` custom `User` model (roles + methods)
- [ ] Verify `products/views.py` imports/usage align with the `User` model
- [ ] Fix any runtime/template issues uncovered by `python manage.py check`
- [ ] Run migrations (`makemigrations`, `migrate`) and ensure DB creates cleanly

## Phase 2: Advanced project structure
- [ ] Move unrelated non-Django demo folders into `legacy/` (keep repo reference)
- [ ] Ensure root README explains how to run the Django project + seed demo

## Phase 3: Quality & requirement coverage
- [ ] Confirm QR content format + verify URL generation works end-to-end
- [ ] Confirm duplicate/clone detection logic matches requirements
- [ ] Ensure alerting code won’t crash without API keys (already best-effort)
- [ ] Run a smoke test: seed_demo + verify a generated unit hash

