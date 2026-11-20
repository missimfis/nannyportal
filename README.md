# nanny webportal
Portal to connect nannies and parents.

## Setup
1. Copy `.env.example` to `.env` and fill in required values (never commit `.env`).
2. Install dependencies: `pip install -r requirements.txt`
3. Apply migrations: `python manage.py migrate`
4. (Optional, recommended for existing data) Backfill search coordinates off the request path: `python manage.py geocode_profiles`
5. Run locally: `python manage.py runserver`

## Security & production configuration
- **Secrets**: `SECRET_KEY`, DB credentials, SMTP credentials, and Stripe keys must come from environment/secret storage. Treat any credential ever committed to git history as exposed and rotate it.
- **HTTPS/proxy/HSTS**: terminate TLS at a trusted reverse proxy/load balancer. Set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, configure `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`, and enable `SECURE_PROXY_SSL_HEADER_ENABLED=True` only if the proxy strips and sets `X-Forwarded-Proto` consistently. Roll out HSTS (`SECURE_HSTS_SECONDS`) in stages after HTTPS is verified end-to-end.
- **Cookies/sessions**: sane defaults are provided (`HttpOnly` session cookies, `SameSite=Lax`, limited session age/rotation, password reset token timeout). Adjust to your policy.
- **Database**: SQLite is for local development only. Use PostgreSQL (or another robust RDBMS) in production; do not run multiple Gunicorn workers against SQLite for real traffic. Configure via `DB_ENGINE`, `DB_NAME`, etc.
- **Backups/DR**: implement automated database backups, encrypted/secured backup storage, restore testing, and migration testing. User-uploaded media and DB storage must be protected and backed up according to policy.
- **Uploads/media**: profile images are validated, size-limited, EXIF-stripped, resized server-side, and stored under a private upload path. Public media serving via Django is disabled outside `DEBUG`; use object storage or a fronting server with access controls in production. User-uploaded photos should not be committed to the repository.
- **Geocoding**: geocoding is off the profile-save request path by default (`GEOCODE_ON_SAVE=False`). Run `python manage.py geocode_profiles` periodically/background to backfill coordinates. Provider/domain and user-agent are configurable; document data sharing and avoid excess precision.
- **Email**: configure SMTP/TLS/host in env. Current delivery uses best-effort background threads outside dev backends; for production durability/retries/monitoring use a real task queue (e.g. Celery/RQ) or a transactional email provider integration.
- **Rate limiting**: in-app cache-backed throttling is included for login/reset/signup/contact/messaging as best-effort protection. Use a shared cache and/or edge/WAF rate limiting in multi-instance deployments.

## Stripe payments
Checkout sessions are created only for authenticated users via POST. A subscription is activated only by the signed Stripe webhook at `/stripe/webhook` after Stripe reports a paid Checkout Session. Configure `STRIPE_WEBHOOK_SECRET` and subscribe to at least:
- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

## Docker (production)
The Docker image runs Gunicorn (not `runserver`). Inject secrets/config via environment at runtime. For real traffic use PostgreSQL and appropriate worker/process architecture; do not rely on container-local filesystem for durable uploads.

## CI
GitHub Actions workflow runs Django checks and tests in `.github/workflows/ci.yml`.

## Tests
```bash
DJANGO_ALLOW_INSECURE_DEFAULTS=1 DEBUG=1 python manage.py test web.tests
```

## Notes on committed media and history
- Files under `web/media/web/images/` may include committed assets with embedded metadata; review consent/licensing for pictured persons and strip sensitive metadata before distribution. Treat this as an operational/content review item.
- Scan git history/blobs for previously committed secrets (e.g. `git log -p --all -S 'SECRET_KEY'`, `gitleaks`/`trufflehog`) and rotate any values that may have been exposed.
