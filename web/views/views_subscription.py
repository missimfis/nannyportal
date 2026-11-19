import logging

import stripe

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView

from web.models.models_subscription import UserSubscription
from ..models import Subscription
from ..models import Price

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(LoginRequiredMixin, View):
    """Start a Stripe Checkout session for an authenticated user.

    A pending subscription is stored locally so the signed Stripe webhook can
    match the payment back to the correct user. The subscription is *not*
    activated here.
    """

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        price = get_object_or_404(Price, pk=self.kwargs["pk"])
        base_url = request.build_absolute_uri('/').rstrip('/')

        user_subscription = UserSubscription.objects.create(
            user=request.user,
            price=price,
        )

        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=base_url + '/success',
                cancel_url=base_url + '/cancel',
                line_items=[
                    {
                        'price': price.stripe_price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                client_reference_id=str(user_subscription.pk),
                metadata={
                    'user_subscription_id': str(user_subscription.pk),
                },
            )
        except Exception:
            user_subscription.delete()
            raise

        user_subscription.stripe_checkout_session_id = checkout_session.id
        user_subscription.save(update_fields=['stripe_checkout_session_id'])
        return redirect(checkout_session.url)


class SuccessView(LoginRequiredMixin, TemplateView):
    """Display the current subscription state without changing it.

    Activation only happens in the Stripe webhook after a verified payment.
    """

    template_name = "web/success.html"

    def get_context_data(self, **kwargs):
        user_subscription = (
            UserSubscription.objects
            .filter(user=self.request.user)
            .select_related('price')
            .order_by('-valid_from', '-pk')
            .first()
        )
        context = super().get_context_data(**kwargs)
        context["subscription"] = user_subscription
        context["user"] = self.request.user
        return context


class CancelView(LoginRequiredMixin, TemplateView):
    template_name = "web/cancel.html"


class SubscriptionPageView(TemplateView):
    template_name = "web/subscription.html"

    def get_context_data(self, **kwargs):
        subscription = Subscription.objects.get(name="Abonnement")
        prices = Price.objects.filter(subscription=subscription)
        context = super().get_context_data(**kwargs)
        context.update({
            "subscription": subscription,
            "prices": prices
        })
        return context


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Verify and process Stripe webhook events.

    Subscriptions are activated only for events whose signature has been
    verified with STRIPE_WEBHOOK_SECRET and whose Checkout Session is paid.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook received but STRIPE_WEBHOOK_SECRET is not configured")
        return HttpResponse(status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.warning("Stripe webhook rejected: invalid payload")
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError:
        logger.warning("Stripe webhook rejected: invalid signature")
        return HttpResponse(status=400)

    event_type = event.get('type')
    if event_type not in (
        'checkout.session.completed',
        'checkout.session.async_payment_succeeded',
    ):
        return HttpResponse(status=200)

    session = event['data']['object']

    if session.get('mode') != 'payment':
        return HttpResponse(status=200)

    if session.get('payment_status') != 'paid':
        logger.info(
            "Stripe Checkout session %s is not paid (status=%s); not activating",
            session.get('id'),
            session.get('payment_status'),
        )
        return HttpResponse(status=200)

    metadata = session.get('metadata') or {}
    subscription_id = (
        metadata.get('user_subscription_id')
        or session.get('client_reference_id')
    )
    if not subscription_id or not str(subscription_id).isdigit():
        logger.warning(
            "Stripe Checkout session %s has an invalid subscription reference %r",
            session.get('id'),
            subscription_id,
        )
        return HttpResponse(status=400)

    with transaction.atomic():
        user_subscription = (
            UserSubscription.objects
            .select_for_update()
            .select_related('price')
            .filter(pk=int(subscription_id))
            .first()
        )
        if user_subscription is None:
            logger.warning(
                "Stripe Checkout session %s references unknown subscription %s",
                session.get('id'),
                subscription_id,
            )
            return HttpResponse(status=200)

        session_id = session.get('id')
        if (user_subscription.stripe_checkout_session_id
                and user_subscription.stripe_checkout_session_id != session_id):
            logger.warning(
                "Stripe Checkout session %s does not match stored session for subscription %s",
                session_id,
                subscription_id,
            )
            return HttpResponse(status=400)

        amount_total = session.get('amount_total')
        if amount_total is None or int(amount_total) != int(user_subscription.price.price):
            logger.warning(
                "Stripe Checkout session %s amount %s does not match price %s",
                session_id,
                amount_total,
                user_subscription.price.price,
            )
            return HttpResponse(status=400)

        if user_subscription.activated:
            return HttpResponse(status=200)

        user_subscription.activated = True
        user_subscription.valid_from = timezone.now()
        if not user_subscription.stripe_checkout_session_id:
            user_subscription.stripe_checkout_session_id = session_id
        user_subscription.save(update_fields=[
            'activated',
            'valid_from',
            'stripe_checkout_session_id',
        ])

    logger.info(
        "Activated subscription %s after verified Stripe payment %s",
        subscription_id,
        session.get('id'),
    )
    return HttpResponse(status=200)
