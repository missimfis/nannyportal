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

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
    return 'web/images/user_{0}/{1}'.format(instance.user.id, filename)

class Profilbild(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    bild = models.ImageField(
        upload_to=user_directory_path, default='web/images/mitarbeiter.png')

# These two auto-delete files from filesystem when they are unneeded:
@receiver(models.signals.post_delete, sender=Profilbild)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.bild and os.path.isfile(instance.bild.path):
        os.remove(instance.bild.path)

@receiver(models.signals.pre_save, sender=Profilbild)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Profilbild.objects.get(pk=instance.pk).bild
    except Profilbild.DoesNotExist:
        return False

    new_file = instance.bild
    if  old_file != new_file and os.path.isfile(old_file.path) and not instance.bild.path.__contains__(old_file.default):
        os.remove(old_file.path)