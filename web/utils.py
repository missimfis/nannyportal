import logging
import math
import threading

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from geopy.distance import geodesic
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Photon

from .image_utils import process_profile_image
from .models import (
    Angabejob,
    BetreuungsZeitEltern,
    Description,
    Descriptioneltern,
    Nachrichten,
    Profil,
    Profilbild,
    Profileltern,
)

logger = logging.getLogger(__name__)

E_MAIL_ADDR = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@nanny25.ch')
KM_PER_DEGREE_LATITUDE = 111.32
DEFAULT_PROFILE_IMAGE = Profilbild._meta.get_field('bild').get_default()


class _GeolocatorProxy:
    def geocode(self, *args, **kwargs):
        return _get_geolocator().geocode(*args, **kwargs)

geolocator = _GeolocatorProxy()


def _get_geolocator():
    return Photon(
        user_agent=getattr(settings, 'GEOCODING_USER_AGENT', 'nannyportal'),
        domain=getattr(settings, 'GEOCODING_DOMAIN', 'photon.komoot.io'),
    )


def anz_neue_nachrichten(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return 0
    return Nachrichten.objects.filter(empfaenger=request.user, gelesen=False).count()


def is_in_distance(point1, point2, distance_km=10):
    try:
        distance = geodesic(point1, point2).km
    except Exception:
        return False
    return distance <= float(distance_km)


from functools import lru_cache


@lru_cache(maxsize=256)
def _geocode_cached(query):
    for attempt in range(3):
        try:
            return geolocator.geocode(query, timeout=2)
        except GeocoderTimedOut:
            if attempt == 2:
                return None
        except GeocoderServiceError:
            return None
        except Exception:
            return None
    return None


def geocode_address(address):
    """Geocode an address. Intended for background/management use, not request path."""
    if not address:
        return None
    query = str(address).strip().lower()
    if not query:
        return None
    return _geocode_cached(query)


def _clear_geocode_cache():
    try:
        _geocode_cached.cache_clear()
    except Exception:
        pass

geocode_address.cache_clear = _clear_geocode_cache


def get_point(location):
    loc = geocode_address(location)
    if loc is None:
        return (0.0, 0.0)
    return (float(loc.latitude), float(loc.longitude))


def update_profile_coordinates(profil, force=False):
    """Geocode and persist coordinates for a profile model instance.

    Off by default in request paths; run via management command or background job.
    """
    if profil is None:
        return (0.0, 0.0)
    if not force and profil.lat and profil.lon and float(profil.lat) != 0.0 and float(profil.lon) != 0.0:
        return (float(profil.lat), float(profil.lon))

    # Use minimal precision/coarse query: PLZ/region/country context if available
    parts = []
    if getattr(profil, 'plz', None):
        parts.append(str(profil.plz))
    if getattr(profil, 'ort', None):
        parts.append(str(profil.ort))
    query = " ".join(p for p in parts if p).strip()
    if not query:
        return (float(profil.lat or 0.0), float(profil.lon or 0.0))

    point = get_point(query)
    if point != (0.0, 0.0):
        profil.lat = point[0]
        profil.lon = point[1]
        try:
            profil.save(update_fields=['lat', 'lon'])
        except Exception:
            # object may be unsaved in some flows
            pass
    return point


def create_and_return_point2(profil):
    """Compatibility wrapper: only geocodes if explicitly enabled."""
    if getattr(settings, 'GEOCODE_ON_SAVE', False):
        return update_profile_coordinates(profil, force=False)
    return (float(getattr(profil, 'lat', 0.0) or 0.0), float(getattr(profil, 'lon', 0.0) or 0.0))


def _bounding_box(point, distance_km):
    lat, lon = point
    distance_km = float(distance_km)
    lat_delta = distance_km / KM_PER_DEGREE_LATITUDE
    lon_scale = KM_PER_DEGREE_LATITUDE * max(abs(math.cos(math.radians(lat))), 0.01)
    lon_delta = distance_km / lon_scale
    return lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta


def _get_search_params(request):
    if request.method != 'POST':
        return None, None
    term = (request.POST.get('term') or '').strip()
    distance = request.POST.get('distance')
    if not term or distance in (None, ''):
        return None, None
    try:
        distance_km = float(distance)
    except (TypeError, ValueError):
        return None, None
    if distance_km <= 0:
        return None, None
    # cap to reasonable radius
    distance_km = min(distance_km, 200.0)
    return term, distance_km


def _resolve_search_origin(term, fallback_profile=None):
    point = get_point(term)
    if point != (0.0, 0.0):
        return point
    # fallback to profile's existing (already geocoded) coords; no external geocode here
    if fallback_profile is not None:
        lat = float(getattr(fallback_profile, 'lat', 0.0) or 0.0)
        lon = float(getattr(fallback_profile, 'lon', 0.0) or 0.0)
        if lat != 0.0 or lon != 0.0:
            return (lat, lon)
    return (0.0, 0.0)


def _filter_user_ids_by_distance(profile_qs, origin, distance_km):
    lat_min, lat_max, lon_min, lon_max = _bounding_box(origin, distance_km)
    candidates = profile_qs.filter(
        lat__gte=lat_min, lat__lte=lat_max,
        lon__gte=lon_min, lon__lte=lon_max,
    ).exclude(lat=0, lon=0).values_list('user_id', 'lat', 'lon')

    user_ids = []
    for user_id, lat, lon in candidates:
        try:
            if is_in_distance(origin, (float(lat), float(lon)), distance_km):
                user_ids.append(user_id)
        except Exception:
            continue
    return user_ids


def get_relevant_nannys(request, *, public_only=True, fallback_profile=None):
    qs = User.objects.filter(groups__name='Nanny', is_active=True)
    profiles = Profil.objects.filter(user__in=qs)
    if public_only:
        profiles = profiles.filter(is_public=True)
        qs = qs.filter(profil__is_public=True)
    term, distance_km = _get_search_params(request)
    qs = qs.order_by('-last_login', '-id')
    if term is None:
        return qs
    origin = _resolve_search_origin(term, fallback_profile=fallback_profile)
    if origin == (0.0, 0.0):
        # Fallback: coarse text match, no external geocoding required
        return qs.filter(
            Q(profil__ort__icontains=term) | Q(profil__plz__icontains=term)
        ).order_by('-last_login', '-id')
    user_ids = _filter_user_ids_by_distance(profiles, origin, distance_km)
    if not user_ids:
        return qs.none()
    return qs.filter(pk__in=user_ids).order_by('-last_login', '-id')


def get_relevant_parents(request, *, public_only=True, fallback_profile=None):
    qs = User.objects.filter(groups__name='Eltern', is_active=True)
    profiles = Profileltern.objects.filter(user__in=qs)
    if public_only:
        profiles = profiles.filter(is_public=True)
        qs = qs.filter(profileltern__is_public=True)
    term, distance_km = _get_search_params(request)
    qs = qs.order_by('-last_login', '-id')
    if term is None:
        return qs
    origin = _resolve_search_origin(term, fallback_profile=fallback_profile)
    if origin == (0.0, 0.0):
        return qs.filter(
            Q(profileltern__ort__icontains=term) | Q(profileltern__plz__icontains=term)
        ).order_by('-last_login', '-id')
    user_ids = _filter_user_ids_by_distance(profiles, origin, distance_km)
    if not user_ids:
        return qs.none()
    return qs.filter(pk__in=user_ids).order_by('-last_login', '-id')


def paginate_list(request, items, amount):
    paginator = Paginator(items, amount)
    page_number = request.GET.get('page', 1)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=1, on_ends=0)
    page_obj = paginator.get_page(page_number)
    return [page_range, page_obj]


def _ensure_default_picture(user_id, pictures):
    if user_id in pictures:
        return pictures[user_id]
    # virtual/default-like placeholder object
    obj = Profilbild(user_id=user_id, bild=DEFAULT_PROFILE_IMAGE)
    pictures[user_id] = obj
    return obj


def get_populated_nannys(users, *, for_owner_ids=None, include_private_fields=False):
    """Populate nanny cards for a page/list of users.

    By default exposes only minimized/public-safe fields.
    """
    nanny_list = list(users)
    user_ids = [u.pk for u in nanny_list]
    if not user_ids:
        return []

    for_owner_ids = set(for_owner_ids or [])
    profiles = {p.user_id: p for p in Profil.objects.filter(user_id__in=user_ids)}
    pictures = {p.user_id: p for p in Profilbild.objects.filter(user_id__in=user_ids)}
    descriptions = {d.user_id: d for d in Description.objects.filter(user_id__in=user_ids)}
    jobs = {j.user_id: j for j in Angabejob.objects.filter(user_id__in=user_ids)}

    populated = []
    without_picture = []
    for nanny in nanny_list:
        profil = profiles.get(nanny.pk)
        description = descriptions.get(nanny.pk)
        angabejob = jobs.get(nanny.pk)
        bild = pictures.get(nanny.pk)
        if profil is None or description is None or angabejob is None:
            continue
        if bild is None:
            bild = Profilbild(user=nanny, bild=DEFAULT_PROFILE_IMAGE)
        is_owner = nanny.pk in for_owner_ids
        entry = {
            'nanny': nanny,
            'profil': profil,
            'bild': bild,
            'description': description,
            'angabejob': angabejob,
            'is_owner': is_owner,
            'display_ort': profil.ort if (is_owner or include_private_fields) else profil.approximate_ort(),
            'display_age': profil.calculate_age() if (is_owner or include_private_fields) else profil.age_range(),
            'show_sensitive': is_owner or include_private_fields,
        }
        if getattr(bild, 'bild', None) and str(bild.bild) != str(DEFAULT_PROFILE_IMAGE):
            populated.append(entry)
        else:
            without_picture.append(entry)
    return populated + without_picture


def get_populated_parents(users, *, for_owner_ids=None, include_private_fields=False):
    parent_list = list(users)
    user_ids = [u.pk for u in parent_list]
    if not user_ids:
        return []

    for_owner_ids = set(for_owner_ids or [])
    profiles = {p.user_id: p for p in Profileltern.objects.filter(user_id__in=user_ids)}
    pictures = {p.user_id: p for p in Profilbild.objects.filter(user_id__in=user_ids)}
    descriptions = {d.user_id: d for d in Descriptioneltern.objects.filter(user_id__in=user_ids)}
    times = {t.user_id: t for t in BetreuungsZeitEltern.objects.filter(user_id__in=user_ids)}

    populated = []
    for parent in parent_list:
        profil = profiles.get(parent.pk)
        description = descriptions.get(parent.pk)
        betreuungszeit = times.get(parent.pk)
        bild = pictures.get(parent.pk)
        if profil is None or description is None or betreuungszeit is None:
            continue
        if bild is None:
            bild = Profilbild(user=parent, bild=DEFAULT_PROFILE_IMAGE)
        is_owner = parent.pk in for_owner_ids
        populated.append({
            'eltern': parent,
            'profil': profil,
            'bild': bild,
            'description': description,
            'betreuungszeit': betreuungszeit,
            'is_owner': is_owner,
            'display_ort': profil.ort if (is_owner or include_private_fields) else profil.approximate_ort(),
            'show_sensitive': is_owner or include_private_fields,
        })
    return populated


def create_profileimage(request, form):
    """Save/replace profile image with validated, stripped, resized content."""
    user = request.user
    bild = form.cleaned_data.get('bild')
    if bild is None:
        return None
    # replace existing
    Profilbild.objects.filter(user=user).delete()
    obj = Profilbild(user=user, bild=bild)
    obj.save()
    return obj


def _send_email_message(message):
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    if backend.endswith('locmem.EmailBackend') or backend.endswith('console.EmailBackend'):
        try:
            message.send(fail_silently=False)
        except Exception:
            logger.exception('Email send failed (sync dev backend)')
        return
    # Durable queueing not configured in-repo; send in background thread best-effort with logging.
    def _runner():
        try:
            message.send(fail_silently=False)
        except Exception:
            logger.exception('Email send failed')

    try:
        t = threading.Thread(target=_runner, daemon=True)
        t.start()
    except Exception:
        try:
            message.send(fail_silently=False)
        except Exception:
            logger.exception('Email send failed (fallback sync)')


def send_new_user_email_jobsearch(to_user):
    if not getattr(to_user, 'email', None):
        return
    name = f"{to_user.first_name} {to_user.last_name[:1]}." if getattr(to_user, 'last_name', '') else to_user.first_name
    message = (
        f"Guten Tag {name}\n"
        "Herzlich Willkommen auf nanny25.ch.\n"
        "Wir wünschen Ihnen viel Erfolg.\n\n"
        "Freundliche Grüsse\nIhr nanny25.ch Team"
    )
    email = EmailMultiAlternatives(
        'Erfolgreiche Registration auf nanny25.ch',
        message,
        E_MAIL_ADDR,
        [to_user.email],
    )
    _send_email_message(email)


def send_new_message_email(to_user, from_user):
    if not getattr(to_user, 'email', None):
        return
    context = {
        'from_user': from_user,
        'to_user': to_user,
    }
    msg_plain = render_to_string("web/E-Mail/Nachricht.txt", context)
    msg_html = render_to_string("web/E-Mail/Nachricht.html", context)
    email = EmailMultiAlternatives(
        'Neue Nachricht auf nanny25.ch',
        msg_plain,
        E_MAIL_ADDR,
        [to_user.email],
    )
    email.attach_alternative(msg_html, "text/html")
    _send_email_message(email)


def send_contact_email(emailaddr, message):
    to_addr = getattr(settings, 'DEFAULT_FROM_EMAIL', E_MAIL_ADDR)
    email = EmailMultiAlternatives(
        'Kontaktformular Anfrage nanny25.ch',
        f"{emailaddr}: {message}",
        E_MAIL_ADDR,
        [to_addr],
    )
    _send_email_message(email)


# Backwards-compatible helpers

def get_search_point_cached(term):
    return get_point(term)


def _filter_users_by_distance(queryset, profile_model, group_name, term, distance_km):
    """Compatibility helper used by existing tests.

    Narrows queryset to users in the given group whose geocoded profile lies
    within distance_km of the geocoded search term.
    """
    point1 = get_point(term)
    if point1 == (0.0, 0.0):
        return queryset.none()
    profiles = profile_model.objects.filter(user__groups__name=group_name)
    user_ids = _filter_user_ids_by_distance(profiles, point1, distance_km)
    if not user_ids:
        return queryset.none()
    return queryset.filter(pk__in=user_ids)
