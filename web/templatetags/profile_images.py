from django import template
from django.conf import settings
from django.urls import reverse

register = template.Library()


@register.filter
def profile_image_url(image_obj):
    """Return a safe URL for a Profilbild instance or image-like object."""
    if not image_obj:
        return settings.MEDIA_URL + 'web/images/mitarbeiter.png'
    try:
        image_id = getattr(image_obj, 'pk', None)
        bild = getattr(image_obj, 'bild', None)
        default_name = None
        try:
            default_name = image_obj._meta.get_field('bild').get_default()
        except Exception:
            default_name = 'web/images/mitarbeiter.png'
        name = getattr(bild, 'name', '') if bild else ''
        # Public/default asset: serve from media/static URL directly
        if name and default_name and str(name) == str(default_name):
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return media_url.rstrip('/') + '/' + str(name).lstrip('/')
        if image_id:
            return reverse('web:serve-profile-image', args=[image_id])
        if bild and getattr(bild, 'url', None):
            return bild.url
        if name:
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return media_url.rstrip('/') + '/' + str(name).lstrip('/')
    except Exception:
        pass
    return settings.MEDIA_URL + 'web/images/mitarbeiter.png'
