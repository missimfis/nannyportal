# nanny webportal
This project is focused to bring nannies and parents who need a nanny together

# Installation
1. clone the repo
2. copy `.env.example` to `.env` and fill in the required values
3. provide an empty db.sqlite file and apply migrations
4. run `python manage.py geocode_profiles` once to backfill search coordinates
5. build the docker container and run it
6. browse the host in browser

# Configuration
All secrets are read from the environment (or `.env`). Do not commit real
credentials. `SECRET_KEY`, `ALLOWED_HOSTS`, the e-mail settings, and the Stripe
settings must be supplied at deploy time.

# Stripe payments
Checkout sessions are created only for authenticated users via POST. A
subscription is activated only by the signed Stripe webhook at
`/stripe/webhook` after Stripe reports a paid Checkout Session. Configure the
webhook endpoint in the Stripe Dashboard and set `STRIPE_WEBHOOK_SECRET` to the
endpoint's signing secret. Subscribe to at least:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

# Security note
The repository previously contained hard-coded API keys in `web/utils.py`.
They have been removed. If those keys were ever live, rotate them with the
provider and audit their usage. Treat any key that was committed to git as
exposed.

# Usage
The Docker image runs the application with gunicorn (not Django's development
server). For local development, use `python manage.py runserver`.

# Contributions
Pullrequests are welcome
