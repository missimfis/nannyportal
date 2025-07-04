from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


class Subscription(models.Model):
    name = models.CharField(max_length=100)
    stripe_product_id = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Price(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    stripe_price_id = models.CharField(max_length=100)
    price = models.IntegerField(default=0)  # cents

    def get_display_price(self):
        return "{0:.2f}".format(self.price / 100)


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.ForeignKey(Price, on_delete=models.DO_NOTHING)
    activated = models.BooleanField(default=False)
    valid_from = models.DateTimeField(default=timezone.now)

    def is_valid(self):
        if not self.activated:
            return False

        if self.price.id == 1:
            month_amount = 1
        elif self.price.id == 2:
            month_amount = 3
        elif self.price.id == 3:
            month_amount = 6
        else:
            return False
        return timezone.now() < (self.valid_from + timezone.timedelta(days=month_amount*31))
