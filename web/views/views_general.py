from django.conf import settings
from django.contrib.auth import login as dj_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.generic.base import TemplateView

from ..forms import ContactForm, NachrichtenForm, RegistrationForm
from ..models import Nachrichten, Profil, Profilbild, Profileltern
from ..utils import (
    anz_neue_nachrichten,
    get_populated_nannys,
    get_relevant_nannys,
    paginate_list,
    send_new_message_email,
    send_contact_email,
)

index_site = 'web:index'

PUBLIC_SIGNUP_GROUPS = {
    'Nanny': 'web:create-profil',
    'Eltern': 'web:create-profil-eltern',
}


def logout_view(request):
    logout(request)
    return redirect(index_site)


def index(request):
    nannys_qs = get_relevant_nannys(request, public_only=True)
    page_range, page_obj = paginate_list(request, nannys_qs, 3)
    nanny_list = get_populated_nannys(page_obj.object_list, include_private_fields=False)
    page_obj.object_list = nanny_list
    context = {
        'nanny_list': page_obj,
        'range': page_range,
    }
    return render(request, 'web/index.html', context)


def register(request):
    return render(request, 'web/register.html', {'register_form': UserCreationForm()})


class ContactView(TemplateView):
    template_name = 'web/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', ContactForm())
        context['sent'] = self.request.GET.get('sent') == '1'
        return context

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            send_contact_email(form.cleaned_data['email'], form.cleaned_data['message'])
            from django.shortcuts import redirect as _redirect
            return _redirect(reverse('web:contact') + '?sent=1')
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class HelpView(TemplateView):
    template_name = "web/help.html"


class AgbView(TemplateView):
    template_name = "web/agb.html"


class DataProtectionView(TemplateView):
    template_name = 'web/dataprotection.html'


class UeberUnsView(TemplateView):
    template_name = 'web/ueberuns.html'


def kasse(request, abo):
    preis = 59.00
    if abo == 1:
        preis = 19.00
    elif abo == 2:
        preis = 29.00
    elif abo == 3:
        preis = 59.00
    return render(request, 'web/Eltern.Profilseite/kasse.html', {'preis': preis})


def create_user(request, group_id):
    group = get_object_or_404(Group, pk=group_id, name__in=PUBLIC_SIGNUP_GROUPS)
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        email = (user.email or form.cleaned_data.get('username') or '').strip().lower()
        user.email = email
        user.username = email
        user.save()
        group.user_set.add(user)
        # ensure minimal profile/picture records
        if group.name == 'Nanny':
            Profil.objects.get_or_create(user=user)
        elif group.name == 'Eltern':
            Profileltern.objects.get_or_create(user=user)
        Profilbild.objects.get_or_create(user=user)
        dj_login(request, user)
        return redirect(PUBLIC_SIGNUP_GROUPS[group.name])
    return render(request, 'web/user.html', {"form": form})


def _can_message(viewer, other):
    if not viewer or not viewer.is_authenticated or not other or not other.is_active:
        return False
    if viewer.pk == other.pk:
        return False
    # Participants must belong to the two marketplace roles and counterpart profile must exist & be public
    viewer_is_nanny = viewer.groups.filter(name='Nanny').exists()
    viewer_is_eltern = viewer.groups.filter(name='Eltern').exists()
    other_is_nanny = other.groups.filter(name='Nanny').exists()
    other_is_eltern = other.groups.filter(name='Eltern').exists()

    if viewer_is_nanny and other_is_eltern:
        return Profileltern.objects.filter(user=other, is_public=True).exists()
    if viewer_is_eltern and other_is_nanny:
        return Profil.objects.filter(user=other, is_public=True).exists()
    # allow existing conversation participants regardless (handled by caller)
    return False


@login_required
@require_http_methods(["GET", "POST"])
def nachrichten(request, empfaenger_id=None):
    current_user = request.user

    if request.method == 'POST' and request.POST.get('delete') == 'True':
        if empfaenger_id is None:
            return redirect('web:nachrichten')
        empfaenger = get_object_or_404(User, pk=empfaenger_id)
        Nachrichten.objects.filter(
            Q(sender=current_user, empfaenger=empfaenger) |
            Q(sender=empfaenger, empfaenger=current_user)
        ).delete()
        return redirect('web:nachrichten')

    empfaenger = None
    pb = None
    if empfaenger_id is not None:
        empfaenger = get_object_or_404(User, pk=empfaenger_id, is_active=True)
        has_existing = Nachrichten.objects.filter(
            Q(sender=current_user, empfaenger=empfaenger) |
            Q(sender=empfaenger, empfaenger=current_user)
        ).exists()
        if not has_existing and not _can_message(current_user, empfaenger):
            raise Http404()
        pb = Profilbild.objects.filter(user=empfaenger).first() or Profilbild(user=empfaenger)

    form = NachrichtenForm(request.POST or None)

    if request.method == 'POST' and empfaenger is not None and form.is_valid():
        has_existing = Nachrichten.objects.filter(
            Q(sender=current_user, empfaenger=empfaenger) |
            Q(sender=empfaenger, empfaenger=current_user)
        ).exists()
        if not has_existing and not _can_message(current_user, empfaenger):
            raise Http404()
        Nachrichten.objects.create(
            sender=current_user,
            empfaenger=empfaenger,
            meldung=form.cleaned_data['meldung'],
            created=timezone.now(),
            gelesen=False,
        )
        send_new_message_email(empfaenger, current_user)
        return redirect('web:nachrichten', empfaenger_id=empfaenger_id)

    page_obj = None
    meldungen = []
    if empfaenger is not None:
        Nachrichten.objects.filter(
            sender=empfaenger,
            empfaenger=current_user,
            gelesen=False,
        ).update(gelesen=True)
        conversation = (
            Nachrichten.objects
            .filter(
                Q(sender=current_user, empfaenger=empfaenger) |
                Q(sender=empfaenger, empfaenger=current_user)
            )
            .select_related('sender', 'empfaenger')
            .order_by('created', 'pk')
        )
        page_obj = Paginator(conversation, 50).get_page(request.GET.get('page', 1))
        meldungen = page_obj

    partner_ids = set(
        Nachrichten.objects.filter(empfaenger=current_user).values_list('sender_id', flat=True)
    )
    partner_ids.update(
        Nachrichten.objects.filter(sender=current_user).values_list('empfaenger_id', flat=True)
    )
    partner_ids.discard(None)

    list_of_interactions = []
    if partner_ids:
        latest_message = Nachrichten.objects.filter(
            Q(sender=current_user, empfaenger_id=OuterRef('pk')) |
            Q(sender_id=OuterRef('pk'), empfaenger=current_user)
        ).order_by('-created', '-pk')

        partners = User.objects.filter(pk__in=partner_ids).annotate(
            last_message_id=Subquery(latest_message.values('id')[:1])
        )
        partners_by_id = {p.pk: p for p in partners}
        last_message_ids = [p.last_message_id for p in partners_by_id.values() if p.last_message_id]
        last_messages = Nachrichten.objects.in_bulk(last_message_ids)
        unread_counts = dict(
            Nachrichten.objects.filter(
                empfaenger=current_user, sender_id__in=partner_ids, gelesen=False,
            ).values_list('sender_id').annotate(count=Count('id'))
        )
        pictures = {p.user_id: p for p in Profilbild.objects.filter(user_id__in=partner_ids)}
        for partner_id, partner in partners_by_id.items():
            last_message = last_messages.get(getattr(partner, 'last_message_id', None))
            if last_message is None:
                continue
            list_of_interactions.append({
                'user': partner,
                'last_message': last_message,
                'new_messages': unread_counts.get(partner_id, 0),
                'bild': pictures.get(partner_id) or Profilbild(user=partner),
            })
        list_of_interactions.sort(key=lambda item: item['last_message'].created, reverse=True)

    group = current_user.groups.values_list('name', flat=True).first()
    pb_me = Profilbild.objects.filter(user=current_user).first() or Profilbild(user=current_user)

    context = {
        "form": form,
        "meldungen": meldungen,
        "page_obj": page_obj,
        "empfaenger_id": empfaenger_id,
        "empfaenger": empfaenger,
        "bild": pb,
        'pbMe': pb_me,
        "list_of_interactions": list_of_interactions,
        "group": group,
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    }
    return render(request, 'web/nachrichten.html', context)


@login_required
@require_POST
def delete_user(request):
    user = request.user
    logout(request)
    user.delete()
    return redirect(index_site)


@login_required
def redirection(request):
    switcher = {
        'Eltern': 'web:startseiteeltern',
        'Nanny': 'web:startseitenanny',
        'Tier Inserat': 'web:tierstartseite',
        'Tier Jobsuchende': 'web:tiersitterstartseite',
        'Senior Inserat': 'web:seniorstartseite',
        'Senior Jobsuchende': 'web:seniorbetreuerstartseite',
        'Admin': '/admin',
    }
    groups = list(request.user.groups.values_list('name', flat=True))
    if groups:
        target = switcher.get(groups[0])
        if target:
            return redirect(target)
    return redirect(index_site)


class SettingsView(TemplateView):
    template_name = "web/einstellungen.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['group'] = user.groups.values_list('name', flat=True).first() if user.is_authenticated else None
        return context


@require_GET
def serve_profile_image(request, image_id):
    """Serve user-uploaded profile images with access control.

    Public profile images may be viewed without authentication when the owner's
    profile is marked public. Private/unpublished images require authentication
    and an appropriate relationship (owner or conversation participant).
    """
    image = get_object_or_404(Profilbild, pk=image_id)
    owner = image.user
    if owner is None:
        raise Http404()

    is_public_profile = Profil.objects.filter(user=owner, is_public=True).exists() or Profileltern.objects.filter(user=owner, is_public=True).exists()
    user = getattr(request, 'user', None)
    is_authenticated = bool(user and user.is_authenticated)

    allowed = is_public_profile
    if not allowed and is_authenticated:
        allowed = user.pk == owner.pk
        if not allowed:
            allowed = Nachrichten.objects.filter(
                Q(sender=user, empfaenger=owner) | Q(sender=owner, empfaenger=user)
            ).exists()
    if not allowed:
        # For non-public profiles, require login/relationship
        if not is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        raise Http404()

    default_name = Profilbild._meta.get_field('bild').get_default()
    bild_name = getattr(image.bild, 'name', '') if image.bild else ''
    # Serve file directly (works in dev and simple deployments). In production a
    # fronting server/object storage can be configured separately.
    try:
        if image.bild and bild_name:
            fileobj = image.bild.open('rb')
            content_type = 'application/octet-stream'
            try:
                # try to guess from storage name
                import mimetypes
                content_type = mimetypes.guess_type(bild_name)[0] or content_type
            except Exception:
                pass
            return FileResponse(fileobj, content_type=content_type)
    except Exception:
        pass
    # fallback for default/missing
    try:
        from django.shortcuts import redirect as dj_redirect
        target = default_name or 'web/images/mitarbeiter.png'
        return dj_redirect(settings.MEDIA_URL.rstrip('/') + '/' + str(target).lstrip('/'))
    except Exception:
        raise Http404()
