from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from web.models import (
    Angabejob,
    Description,
    Nachrichten,
    Price,
    Profil,
    Profilbild,
    Subscription,
    UserSubscription,
)
from web.utils import (
    _filter_users_by_distance,
    geocode_address,
    get_point,
    get_populated_nannys,
    is_in_distance,
)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    STRIPE_SECRET_KEY="sk_test_secret",
    STRIPE_WEBHOOK_SECRET="whsec_test",
)
class PaymentSecurityTests(TestCase):
    def setUp(self):
        self.subscription = Subscription.objects.create(
            name="Abonnement",
            stripe_product_id="prod_test",
        )
        self.price = Price.objects.create(
            subscription=self.subscription,
            stripe_price_id="price_test",
            price=1900,
        )
        self.user = User.objects.create_user(
            username="paid@example.com",
            email="paid@example.com",
            password="Sup3rS3cret!42",
        )
        self.client.force_login(self.user)

    def checkout_url(self):
        return reverse("web:create-checkout-session", args=[self.price.pk])

    def webhook_event(self, **overrides):
        event = {
            "id": "evt_test",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "mode": "payment",
                    "payment_status": "paid",
                    "amount_total": self.price.price,
                    "client_reference_id": None,
                    "metadata": {},
                }
            },
        }
        session = event["data"]["object"]
        session.update(overrides)
        return event

    def post_webhook(self, event, signature="sig_test"):
        import json

        payload = json.dumps(event).encode()
        return self.client.post(
            reverse("web:stripe-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )

    def test_checkout_requires_post(self):
        response = self.client.get(self.checkout_url())
        self.assertEqual(response.status_code, 405)
        self.assertEqual(UserSubscription.objects.count(), 0)

    def test_checkout_requires_authentication(self):
        response = Client().post(self.checkout_url())
        self.assertRedirects(
            response,
            f"{settings.LOGIN_URL}?next={self.checkout_url()}",
            fetch_redirect_response=False,
        )
        self.assertEqual(UserSubscription.objects.count(), 0)

    @patch("web.views.views_subscription.stripe.checkout.Session.create")
    def test_checkout_creates_pending_subscription_only(self, create_session):
        create_session.return_value = SimpleNamespace(
            id="cs_test",
            url="https://checkout.stripe.com/c/pay/cs_test",
        )

        response = self.client.post(self.checkout_url())

        self.assertRedirects(
            response,
            "https://checkout.stripe.com/c/pay/cs_test",
            fetch_redirect_response=False,
        )
        subscription = UserSubscription.objects.get()
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.price, self.price)
        self.assertFalse(subscription.activated)
        self.assertEqual(subscription.stripe_checkout_session_id, "cs_test")

        kwargs = create_session.call_args.kwargs
        self.assertEqual(kwargs["client_reference_id"], str(subscription.pk))
        self.assertEqual(
            kwargs["metadata"]["user_subscription_id"],
            str(subscription.pk),
        )
        self.assertEqual(kwargs["line_items"][0]["price"], "price_test")
        self.assertEqual(kwargs["success_url"], "http://testserver/success")
        self.assertEqual(kwargs["cancel_url"], "http://testserver/cancel")

    def test_success_page_does_not_activate_subscription(self):
        subscription = UserSubscription.objects.create(
            user=self.user,
            price=self.price,
            activated=False,
        )

        response = self.client.get(reverse("web:success"))

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertFalse(subscription.activated)

    def test_webhook_rejects_invalid_signature(self):
        error = stripe.SignatureVerificationError("bad signature", "sig_test")
        with patch(
            "web.views.views_subscription.stripe.Webhook.construct_event",
            side_effect=error,
        ):
            response = self.post_webhook(self.webhook_event())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserSubscription.objects.count(), 0)

    def test_webhook_requires_secret_configuration(self):
        with override_settings(STRIPE_WEBHOOK_SECRET=None):
            response = self.post_webhook(self.webhook_event())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(UserSubscription.objects.count(), 0)

    @patch("web.views.views_subscription.stripe.Webhook.construct_event")
    def test_webhook_ignores_unpaid_session(self, construct_event):
        construct_event.return_value = self.webhook_event(
            payment_status="unpaid",
        )
        subscription = UserSubscription.objects.create(
            user=self.user,
            price=self.price,
        )

        response = self.post_webhook(construct_event.return_value)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            construct_event.call_args.args[2],
            "whsec_test",
        )
        subscription.refresh_from_db()
        self.assertFalse(subscription.activated)

    @patch("web.views.views_subscription.stripe.Webhook.construct_event")
    def test_webhook_activates_only_after_verified_payment(self, construct_event):
        event = self.webhook_event(
            client_reference_id=None,
            metadata={"user_subscription_id": "placeholder"},
        )
        construct_event.return_value = event
        old_valid_from = timezone.now() - timedelta(days=10)
        subscription = UserSubscription.objects.create(
            user=self.user,
            price=self.price,
            activated=False,
            valid_from=old_valid_from,
        )
        event["data"]["object"]["client_reference_id"] = str(subscription.pk)
        event["data"]["object"]["metadata"]["user_subscription_id"] = str(
            subscription.pk
        )

        response = self.post_webhook(event)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            construct_event.call_args.args[2],
            "whsec_test",
        )
        subscription.refresh_from_db()
        self.assertTrue(subscription.activated)
        self.assertGreater(subscription.valid_from, old_valid_from)
        self.assertEqual(subscription.stripe_checkout_session_id, "cs_test")

    @patch("web.views.views_subscription.stripe.Webhook.construct_event")
    def test_webhook_rejects_amount_mismatch(self, construct_event):
        event = self.webhook_event(amount_total=self.price.price + 1)
        construct_event.return_value = event
        subscription = UserSubscription.objects.create(
            user=self.user,
            price=self.price,
        )
        event["data"]["object"]["metadata"]["user_subscription_id"] = str(
            subscription.pk
        )

        response = self.post_webhook(event)

        self.assertEqual(response.status_code, 400)
        subscription.refresh_from_db()
        self.assertFalse(subscription.activated)

    @patch("web.views.views_subscription.stripe.Webhook.construct_event")
    def test_webhook_rejects_session_mismatch(self, construct_event):
        event = self.webhook_event(id="cs_test")
        construct_event.return_value = event
        subscription = UserSubscription.objects.create(
            user=self.user,
            price=self.price,
            stripe_checkout_session_id="cs_another",
        )
        event["data"]["object"]["metadata"]["user_subscription_id"] = str(
            subscription.pk
        )

        response = self.post_webhook(event)

        self.assertEqual(response.status_code, 400)
        subscription.refresh_from_db()
        self.assertFalse(subscription.activated)

    @patch("web.views.views_subscription.stripe.Webhook.construct_event")
    def test_webhook_rejects_invalid_subscription_reference(self, construct_event):
        construct_event.return_value = self.webhook_event(metadata={
            "user_subscription_id": "not-an-id",
        })

        response = self.post_webhook(construct_event.return_value)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserSubscription.objects.count(), 0)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class SignupTests(TestCase):
    def setUp(self):
        self.nanny_group = Group.objects.create(name="Nanny")
        self.parent_group = Group.objects.create(name="Eltern")
        self.admin_group = Group.objects.create(name="Admins")

    def registration_data(self, email="signup@example.com"):
        return {
            "first_name": "Test",
            "last_name": "Person",
            "username": email,
            "password1": "Sup3rS3cret!42",
            "password2": "Sup3rS3cret!42",
        }

    def test_non_public_group_is_rejected_and_not_created(self):
        other_group = Group.objects.create(name="Other")
        response = self.client.post(
            reverse("web:create-user", args=[other_group.pk]),
            self.registration_data("other@example.com"),
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(User.objects.filter(username="other@example.com").exists())
        self.assertEqual(Group.objects.filter(name="Other").count(), 1)

    def test_admin_group_is_rejected(self):
        response = self.client.post(
            reverse("web:create-user", args=[self.admin_group.pk]),
            self.registration_data("admin@example.com"),
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(User.objects.filter(username="admin@example.com").exists())

    def test_public_group_signup_is_allowed(self):
        response = self.client.post(
            reverse("web:create-user", args=[self.nanny_group.pk]),
            self.registration_data(),
        )

        self.assertRedirects(
            response,
            reverse("web:create-profil"),
            fetch_redirect_response=False,
        )
        user = User.objects.get(username="signup@example.com")
        self.assertEqual(list(user.groups.all()), [self.nanny_group])
        self.assertIn("_auth_user_id", self.client.session)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class AccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="delete@example.com",
            password="Sup3rS3cret!42",
        )
        self.client.force_login(self.user)

    def test_delete_user_requires_post(self):
        response = self.client.get(reverse("web:delete-user"))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_user_requires_authentication(self):
        response = Client().post(reverse("web:delete-user"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_post_deletes_account_and_logs_out(self):
        response = self.client.post(reverse("web:delete-user"))

        self.assertRedirects(
            response,
            reverse("web:index"),
            fetch_redirect_response=False,
        )
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_view_logs_user_out(self):
        self.assertIn("_auth_user_id", self.client.session)

        self.client.get(reverse("web:logout_view"))

        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class InboxTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Eltern")
        self.user = User.objects.create_user(
            username="inbox@example.com",
            password="Sup3rS3cret!42",
        )
        self.user.groups.add(self.group)
        self.other = User.objects.create_user(
            username="other@example.com",
            password="Sup3rS3cret!42",
        )
        self.client.force_login(self.user)

    def conversation_url(self):
        return reverse("web:nachrichten", args=[self.other.pk])

    @patch("web.views.views_general.send_new_message_email")
    def test_conversation_deletion_requires_post(self, _send_email):
        Nachrichten.objects.create(
            sender=self.other,
            empfaenger=self.user,
            meldung="Hallo",
        )

        response = self.client.get(self.conversation_url() + "?delete=True")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Nachrichten.objects.count(), 1)

        response = self.client.post(self.conversation_url(), {"delete": "True"})
        self.assertRedirects(
            response,
            reverse("web:nachrichten"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Nachrichten.objects.count(), 0)

    def test_conversation_messages_are_paginated(self):
        for number in range(60):
            Nachrichten.objects.create(
                sender=self.other,
                empfaenger=self.user,
                meldung=f"Nachricht {number}",
            )

        response = self.client.get(self.conversation_url())

        self.assertEqual(response.status_code, 200)
        page = response.context["meldungen"]
        self.assertEqual(len(page), 50)
        self.assertEqual(page.paginator.num_pages, 2)


class SearchPerformanceTests(TestCase):
    def setUp(self):
        geocode_address.cache_clear()

    def tearDown(self):
        geocode_address.cache_clear()

    def create_nanny(self, username, lat=47.3769, lon=8.5417):
        nanny_group, _ = Group.objects.get_or_create(name="Nanny")
        user = User.objects.create_user(username=username, password="pw")
        user.groups.add(nanny_group)
        Profil.objects.create(
            user=user,
            plz=8000,
            ort="Zürich",
            birth_date=timezone.now(),
            salary=20,
            lat=lat,
            lon=lon,
        )
        return user

    @patch("web.utils.geolocator.geocode")
    def test_geocoding_results_are_cached(self, geocode):
        geocode.return_value = SimpleNamespace(
            latitude=47.3769,
            longitude=8.5417,
        )

        self.assertEqual(get_point("Zürich"), (47.3769, 8.5417))
        self.assertEqual(get_point("zürich"), (47.3769, 8.5417))

        geocode.assert_called_once_with("zürich", timeout=2)

    @patch("web.utils.get_point", return_value=(47.3769, 8.5417))
    def test_distance_search_narrows_candidates(self, _get_point):
        near = self.create_nanny("near@example.com")
        self.create_nanny("far@example.com", lat=48.2, lon=11.5)
        nannys = User.objects.filter(groups__name="Nanny")

        with patch(
            "web.utils.is_in_distance",
            wraps=is_in_distance,
        ) as distance_check:
            result = _filter_users_by_distance(
                nannys,
                Profil,
                "Nanny",
                "Zürich",
                10,
            )

        self.assertEqual(list(result), [near])
        self.assertEqual(distance_check.call_count, 1)

    def test_populated_nannys_use_batched_queries(self):
        for number in range(3):
            user = self.create_nanny(f"nanny{number}@example.com")
            Profilbild.objects.create(user=user)
            Description.objects.create(user=user)
            Angabejob.objects.create(
                user=user,
                angabe_job_nanny=True,
                angabe_job_tagesmutter=False,
            )
        nannys = User.objects.filter(groups__name="Nanny").order_by("-last_login")

        with self.assertNumQueries(5):
            populated = get_populated_nannys(nannys)

        self.assertEqual(len(populated), 3)
