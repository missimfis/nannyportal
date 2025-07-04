import functools
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
import threading
from threading import Thread


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)


keys = ["3P1o7XnrbgdMmtGluNCh4ZylZdMGqpLa", "cxNc1TDVQDjTHAIiZyrRYe8ZvrKmvkPj"]
geolocator = Photon(user_agent="web", domain='photon.komoot.io')

E_MAIL_ADDR = 'info@nanny25.ch'


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
    return distance <= int(distance_km)


def get_point(location):
    loc = do_geocode(location)
    if loc is None:
        return (0, 0)
    return (loc.latitude, loc.longitude)


def do_geocode(address, attempt=1, max_attempts=2):
    try:
        return geolocator.geocode(address, timeout=2)
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return do_geocode(address, attempt=attempt+1)
        raise


def create_and_return_point2(profil):
    point2 = (profil.lat, profil.lon)
    if profil.lat == 0.0:
        point2 = get_point(profil.ort)
        profil.lat = point2[0]
        profil.lon = point2[1]
        profil.save()
    return point2


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
    term = None
    if request.POST is not None:
        term = request.POST.get('term')
        distance = request.POST.get('distance')
        if term is not None and distance is not None:
            nannyprofile = Profil.objects.all()
            nannys_in_range = []
            point1 = get_point(term)
            for profil in nannyprofile:
                location = profil.ort
                point2 = create_and_return_point2(profil)
                if location is not None and is_in_distance(point1, point2, distance):
                    nannys_in_range.append(profil.user.id)
            if len(nannys_in_range) > 0:
                nannys = User.objects.filter(
                    groups__name='Nanny', pk__in=nannys_in_range).order_by('-last_login')
    return nannys


def get_populated_nannys(nannys):
    list_of_populated_nannys = []
    nannys_ohne_bild = []
    if nannys is not None:
        for nanny in nannys:
            li_profil = Profil.objects.filter(user=nanny).first()
            li_bild = Profilbild.objects.filter(user=nanny).first()
            li_description = Description.objects.filter(user=nanny).first()
            li_angabejob = Angabejob.objects.filter(user=nanny).first()
            if li_profil is not None and li_bild is not None and li_description is not None and li_angabejob is not None:
                if li_bild._meta.get_field('bild').get_default() == li_bild.bild:
                    nannys_ohne_bild.append({
                        'nanny': nanny,
                        'profil': li_profil,
                        'bild': li_bild,
                        'description': li_description,
                        'angabejob': li_angabejob
                    })
                else:
                    list_of_populated_nannys.append({
                        'nanny': nanny,
                        'profil': li_profil,
                        'bild': li_bild,
                        'description': li_description,
                        'angabejob': li_angabejob
                    })
    if len(nannys_ohne_bild) > 0:
        list_of_populated_nannys.extend(nannys_ohne_bild)
    return list_of_populated_nannys


def create_profileimage(request, form):
    if Profilbild.objects.filter(user=request.user) != None:
        Profilbild.objects.filter(user=request.user).delete()
    bild = form.cleaned_data.get("bild")
    Profilbild.objects.create(
        user=request.user,
        bild=bild
    ).save()
