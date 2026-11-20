import os

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver


class Nachrichten(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sender", default=None, null=True, blank=True)
    empfaenger = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="empfaenger", default=None, null=True, blank=True)
    meldung = models.CharField(max_length=1024)
    created = models.DateTimeField('created', default=timezone.now)
    gelesen = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['empfaenger', 'gelesen']),
            models.Index(fields=['sender', 'empfaenger', 'created']),
        ]


def user_directory_path(instance, filename):
    # Store user uploads in private media area (served via authenticated view, not static)
    return 'private/profile_images/user_{0}/{1}'.format(instance.user.id, filename)


class Profilbild(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    bild = models.ImageField(
        upload_to=user_directory_path, default='web/images/mitarbeiter.png')

    def is_default(self):
        try:
            default = self._meta.get_field('bild').get_default()
            return not self.bild or self.bild.name == default
        except Exception:
            return False


@receiver(models.signals.post_delete, sender=Profilbild)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    try:
        if instance.bild and instance.bild.name and not instance.is_default():
            storage = instance.bild.storage
            if storage.exists(instance.bild.name):
                storage.delete(instance.bild.name)
    except Exception:
        pass


@receiver(models.signals.pre_save, sender=Profilbild)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Profilbild.objects.get(pk=instance.pk)
    except Profilbild.DoesNotExist:
        return
    try:
        old_file = old.bild
        new_file = instance.bild
        if old_file and old_file.name != new_file.name and not old.is_default():
            if old_file.storage.exists(old_file.name):
                old_file.storage.delete(old_file.name)
    except Exception:
        pass
