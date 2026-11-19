import functools
import math

from geopy.geocoders import Photon
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut
from django.core.exceptions import (ImproperlyConfigured, ValidationError)
from django.core.paginator import Paginator
from django.utils.module_loading import import_string
from django.conf import settings
from django.core.mail import (EmailMessage, EmailMultiAlternatives)
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from .models import Nachrichten
from .models import Profil
from .models import Description
from .models import Angabejob
from .models import Profilbild
from .models import Profileltern
from .models import Descriptioneltern
from .models import BetreuungsZeitEltern
import threading
from threading import Thread


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)


geolocator = Photon(user_agent="web", domain='photon.komoot.io')

E_MAIL_ADDR = 'info@nanny25.ch'

KM_PER_DEGREE_LATITUDE = 111.32


def anz_neue_nachrichten(request):
    current_user = request.user
    nachrichten = Nachrichten.objects.filter(
        empfaenger=current_user, gelesen=False)
    if nachrichten == None:
        return 0
    else:
        return nachrichten.count()


@functools.lru_cache(maxsize=None)
def get_default_password_validators():
    return get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)


def get_password_validators(validator_config):
    validators = []
    for validator in validator_config:
        try:
            klass = import_string(validator['NAME'])
        except ImportError:
            msg = "The module in NAME could not be imported: %s. Check your AUTH_PASSWORD_VALIDATORS setting."
            raise ImproperlyConfigured(msg % validator['NAME'])
        validators.append(klass(**validator.get('OPTIONS', {})))

    return validators


def validate_password(password, user=None, password_validators=None):
    """
    Validate whether the password meets all validator requirements.

    If the password is valid, return ``None``.
    If the password is invalid, raise ValidationError with all error messages.
    """
    errors = []
    if password_validators is None:
        password_validators = get_default_password_validators()
    for validator in password_validators:
        try:
            validator.validate(password, user)
        except ValidationError as error:
            errors.append(error)
    if errors:
        raise ValidationError(errors)


def is_in_distance(point1, point2, distance_km=10):
    distance = round(geodesic(point1, point2).km, 2)
    return distance <= float(distance_km)


@functools.lru_cache(maxsize=2048)
def geocode_address(address):
    """Geocode an address once per process and cache the result.

    Geocoding is deliberately not done in the search request path. Profiles
    are geocoded when their address is saved (and by the geocode_profiles
    management command for existing rows).
    """
    for attempt in range(3):
        try:
            return geolocator.geocode(address, timeout=2)
        except GeocoderTimedOut:
            if attempt == 2:
                return None
    return None


def get_point(location):
    if not location:
        return (0.0, 0.0)
    loc = geocode_address(location.strip().lower())
    if loc is None:
        return (0.0, 0.0)
    return (float(loc.latitude), float(loc.longitude))


def create_and_return_point2(profil):
    if profil.lat and profil.lon:
        return (float(profil.lat), float(profil.lon))
    point2 = get_point(profil.ort)
    if point2 != (0.0, 0.0):
        profil.lat = point2[0]
        profil.lon = point2[1]
        profil.save(update_fields=['lat', 'lon'])
    return point2


def _bounding_box(point, distance_km):
    """Return a conservative lat/lon box around point for a radius."""
    lat, lon = point
    lat_delta = distance_km / KM_PER_DEGREE_LATITUDE
    lon_delta = distance_km / (
        KM_PER_DEGREE_LATITUDE * max(abs(math.cos(math.radians(lat))), 0.01)
    )
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
    return term, distance_km


def _filter_users_by_distance(queryset, profile_model, group_name, term, distance_km):
    point1 = get_point(term)
    if point1 == (0.0, 0.0):
        return queryset.none()

    lat_min, lat_max, lon_min, lon_max = _bounding_box(point1, distance_km)
    candidates = profile_model.objects.filter(
        user__groups__name=group_name,
        lat__gte=lat_min,
        lat__lte=lat_max,
        lon__gte=lon_min,
        lon__lte=lon_max,
    ).values_list('user_id', 'lat', 'lon')

    user_ids = [
        user_id
        for user_id, lat, lon in candidates
        if is_in_distance(point1, (float(lat), float(lon)), distance_km)
    ]
    if not user_ids:
        return queryset.none()
    return queryset.filter(pk__in=user_ids)


def send_new_user_email_jobsearch(to_user):
    name = to_user.first_name + ' ' + to_user.last_name[:1] + '.'
    message = 'Guten Tag Herr/Frau ' + name + \
        '\n'+'Herzlich Wilkommen auf nanny25.ch.'
    message += '\n' + 'Es freut und Sie auf unserer Plattform begrüssen zu dürfen.'
    message += '\n' + 'Wir wünschen Ihnen viel Erfolg bei der Jobsuche.'
    message += '\n' + 'Freundliche Grüsse'
    message += '\n' + 'Ihr nanny25.ch Team'
    email = EmailMessage(
        'Erfolgreiche Registration auf nanny25.ch',
        message,
        E_MAIL_ADDR,
        [to_user.email],
    )
    EmailThread(email).start()


def send_new_message_email(to_user, from_user):
    context = {
        'from_user': from_user,
        'to_user': to_user
    }
    txt_mail_template = "web/E-Mail/Nachricht.txt"
    html_mail_template = "web/E-Mail/Nachricht.html"
    subject = 'Neue Nachricht auf nanny25.ch'
    send_mail_templates(to_user.email, subject,
                        txt_mail_template, html_mail_template, context)


def send_contact_email(emailaddr, message):
    email = EmailMessage(
        'Kontakformular Anfrage nanny25.ch',
        emailaddr + ": " + message,
        E_MAIL_ADDR,
        [E_MAIL_ADDR],
    )
    EmailThread(email).start()


def send_mail_templates(to, subject, plaintext_file, html_file, context):
    msg_plain = render_to_string(plaintext_file, context)
    msg_html = render_to_string(html_file, context)

    email = EmailMultiAlternatives(
        subject,
        msg_plain,
        E_MAIL_ADDR,
        [to],
    )
    email.attach_alternative(msg_html, "text/html")
    EmailThread(email).start()


def paginate_list(request, paginate_list, amount):
    paginator = Paginator(paginate_list, amount)  # Show 25 contacts per page.

    page_number = request.GET.get('page', 1)
    page_range = paginator.get_elided_page_range(
        number=page_number, on_each_side=1, on_ends=0)
    page_obj = paginator.get_page(page_number)
    return [page_range, page_obj]


def get_relevant_nannys(request):
    nannys = User.objects.filter(groups__name='Nanny').order_by('-last_login')
    term, distance_km = _get_search_params(request)
    if term is None:
        return nannys
    return _filter_users_by_distance(nannys, Profil, 'Nanny', term, distance_km)


def get_relevant_parents(request):
    parents = User.objects.filter(groups__name='Eltern').order_by('-last_login')
    term, distance_km = _get_search_params(request)
    if term is None:
        return parents
    return _filter_users_by_distance(parents, Profileltern, 'Eltern', term, distance_km)


def get_populated_nannys(nannys):
    nanny_list = list(nannys)
    user_ids = [nanny.pk for nanny in nanny_list]
    if not user_ids:
        return []

    profiles = {
        profile.user_id: profile
        for profile in Profil.objects.filter(user_id__in=user_ids)
    }
    pictures = {
        picture.user_id: picture
        for picture in Profilbild.objects.filter(user_id__in=user_ids)
    }
    descriptions = {
        description.user_id: description
        for description in Description.objects.filter(user_id__in=user_ids)
    }
    jobs = {
        job.user_id: job
        for job in Angabejob.objects.filter(user_id__in=user_ids)
    }

    default_image = Profilbild._meta.get_field('bild').get_default()
    populated = []
    without_picture = []

    for nanny in nanny_list:
        profil = profiles.get(nanny.pk)
        bild = pictures.get(nanny.pk)
        description = descriptions.get(nanny.pk)
        angabejob = jobs.get(nanny.pk)
        if profil is None or bild is None or description is None or angabejob is None:
            continue

        entry = {
            'nanny': nanny,
            'profil': profil,
            'bild': bild,
            'description': description,
            'angabejob': angabejob,
        }
        if bild.bild == default_image:
            without_picture.append(entry)
        else:
            populated.append(entry)

    return populated + without_picture


def get_populated_parents(parents):
    parent_list = list(parents)
    user_ids = [parent.pk for parent in parent_list]
    if not user_ids:
        return []

    profiles = {
        profile.user_id: profile
        for profile in Profileltern.objects.filter(user_id__in=user_ids)
    }
    pictures = {
        picture.user_id: picture
        for picture in Profilbild.objects.filter(user_id__in=user_ids)
    }
    descriptions = {
        description.user_id: description
        for description in Descriptioneltern.objects.filter(user_id__in=user_ids)
    }
    times = {
        time.user_id: time
        for time in BetreuungsZeitEltern.objects.filter(user_id__in=user_ids)
    }

    populated = []
    for parent in parent_list:
        profil = profiles.get(parent.pk)
        bild = pictures.get(parent.pk)
        description = descriptions.get(parent.pk)
        betreuungszeit = times.get(parent.pk)
        if (profil is None or bild is None or description is None
                or betreuungszeit is None):
            continue
        populated.append({
            'eltern': parent,
            'profil': profil,
            'bild': bild,
            'description': description,
            'betreuungszeit': betreuungszeit,
        })
    return populated


def create_profileimage(request, form):
    if Profilbild.objects.filter(user=request.user) != None:
        Profilbild.objects.filter(user=request.user).delete()
    bild = form.cleaned_data.get("bild")
    Profilbild.objects.create(
        user=request.user,
        bild=bild
    ).save()
