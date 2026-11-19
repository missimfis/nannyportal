from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth import login as dj_login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.db.models import Count, OuterRef, Q, Subquery
from ..forms import RegistrationForm
from ..forms import NachrichtenForm
from ..models import Nachrichten
from ..models import Profilbild

from ..utils import anz_neue_nachrichten, get_populated_nannys, get_relevant_nannys, paginate_list
from ..utils import send_new_message_email

index_site = 'web:index'

# Only these roles may be selected by a public signup request.
PUBLIC_SIGNUP_GROUPS = {
    'Nanny': 'web:create-profil',
    'Eltern': 'web:create-profil-eltern',
}


def logout_view(request):
    logout(request)
    return redirect(index_site)


def index(request):
    nannys = get_relevant_nannys(request)

    pagination = paginate_list(request, get_populated_nannys(nannys), 3)
    context = {
        'nanny_list': pagination[1],
        'range': pagination[0]
    }
    return render(request, 'web/index.html', context)


def register(request):
    register_form = UserCreationForm()
    return render(request, 'web/register.html', {'register_form': register_form})


class ContactView(TemplateView):
    template_name =  'web/contact.html'

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
    if(abo == 1):
        preis = 19.00
    elif (abo == 2):
        preis = 29.00
    elif (abo == 3):
        preis = 59.00
    context = {
        'preis': preis
    }
    return render(request, 'web/Eltern.Profilseite/kasse.html', context)

def create_user(request, group_id):
    # Never create or assign a group chosen by the caller. Only the explicit
    # public signup roles are accepted; anything else is a 404.
    group = get_object_or_404(
        Group,
        pk=group_id,
        name__in=PUBLIC_SIGNUP_GROUPS,
    )

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.username = user.email
        user.save()
        group.user_set.add(user)
        dj_login(request, user)
        return redirect(PUBLIC_SIGNUP_GROUPS[group.name])
    context = {
        "form": form
    }
    return render(request, 'web/user.html', context)


@login_required
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
        empfaenger = get_object_or_404(User, pk=empfaenger_id)
        pb = Profilbild.objects.filter(user=empfaenger).first()

    form = NachrichtenForm(request.POST or None)

    if request.method == 'POST' and empfaenger is not None and form.is_valid():
        Nachrichten.objects.create(
            sender=current_user,
            empfaenger=empfaenger,
            meldung=form.cleaned_data['meldung'],
            created=timezone.now(),
            gelesen=False,
        )
        send_new_message_email(empfaenger, current_user)
        return redirect('web:nachrichten', empfaenger_id=empfaenger_id)

    # Load only one bounded page of the conversation, not the whole history.
    page_obj = None
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
    else:
        meldungen = []

    # Conversation summaries are fetched in batches rather than per sender.
    partner_ids = set(
        Nachrichten.objects.filter(empfaenger=current_user)
        .values_list('sender_id', flat=True)
    )
    partner_ids.update(
        Nachrichten.objects.filter(sender=current_user)
        .values_list('empfaenger_id', flat=True)
    )
    partner_ids.discard(None)

    list_of_interactions = []
    if partner_ids:
        latest_message = Nachrichten.objects.filter(
            Q(sender=current_user, empfaenger_id=OuterRef('pk')) |
            Q(sender_id=OuterRef('pk'), empfaenger=current_user)
        ).order_by('-created', '-pk')

        partners = (
            User.objects.filter(pk__in=partner_ids)
            .annotate(last_message_id=Subquery(latest_message.values('id')[:1]))
        )
        partners_by_id = {partner.pk: partner for partner in partners}
        last_message_ids = [
            partner.last_message_id
            for partner in partners_by_id.values()
            if partner.last_message_id is not None
        ]
        last_messages = Nachrichten.objects.in_bulk(last_message_ids)
        unread_counts = dict(
            Nachrichten.objects.filter(
                empfaenger=current_user,
                sender_id__in=partner_ids,
                gelesen=False,
            )
            .values_list('sender_id')
            .annotate(count=Count('id'))
        )
        pictures = {
            picture.user_id: picture
            for picture in Profilbild.objects.filter(user_id__in=partner_ids)
        }

        for partner_id, partner in partners_by_id.items():
            last_message = last_messages.get(partner.last_message_id)
            if last_message is None:
                continue
            list_of_interactions.append({
                'user': partner,
                'last_message': last_message,
                'new_messages': unread_counts.get(partner_id, 0),
                'bild': pictures.get(partner_id),
            })
        list_of_interactions.sort(
            key=lambda item: item['last_message'].created,
            reverse=True,
        )

    group = current_user.groups.values_list('name', flat=True).first()
    pb_me = Profilbild.objects.filter(user=current_user).first()

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
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
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
    groups = request.user.groups.values_list('name', flat=True)
    if(len(groups) > 0):
        return redirect(switcher.get(groups[0]))
    else:
        return redirect("/")


class SettingsView(TemplateView):
    template_name = "web/einstellungen.html"

    def get_context_data(self, **kwargs):
        currentuser = self.request.user
        group = self.request.user.groups.values_list('name', flat=True).first()
        context = super(SettingsView, self).get_context_data(**kwargs)
        context['user'] = currentuser
        context['group'] =  group
        return context
