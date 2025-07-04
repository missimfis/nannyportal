import stripe

from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from django.views.generic.base import TemplateView

from web.models.models_subscription import UserSubscription
from ..models import Subscription
from ..models import Price

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(View):
    def get(self, request, *args, **kwargs):
        base_url = request.build_absolute_uri('/')[:-1].strip("/")
        price = Price.objects.get(id=self.kwargs["pk"])
        checkout_session = stripe.checkout.Session.create(
            success_url=base_url + '/success',
            cancel_url=base_url + '/cancel',
            line_items=[
                {
                    'price': price.stripe_price_id,
                    'quantity': 1,
                },
            ],
            customer_email=request.user.email,
            mode='payment',
        )
        UserSubscription.objects.create(user=request.user, price=price)
        return redirect(checkout_session.url)


class SuccessView(TemplateView):
    template_name = "web/success.html"

    def get_context_data(self, **kwargs):
        user_subscription = UserSubscription.objects.get(user=self.request.user)
        user_subscription.activated = True
        user_subscription.save()
        context = super(SuccessView, self).get_context_data(**kwargs)
        context["subscription"] = user_subscription
        context["user"] = self.request.user
        return context


class CancelView(TemplateView):
    template_name = "web/cancel.html"

    def get_context_data(self, **kwargs):
        user_subscription = self.request.user.UserSubscription
        user_subscription.delete()
        context = super(CancelView, self).get_context_data(**kwargs)
        return context


class SubscriptionPageView(TemplateView):
    template_name = "web/subscription.html"

    def get_context_data(self, **kwargs):
        subscription = Subscription.objects.get(name="Abonnement")
        prices = Price.objects.filter(subscription=subscription)
        context = super(SubscriptionPageView, self).get_context_data(**kwargs)
        context.update({
            "subscription": subscription,
            "prices": prices
        })
        return context
