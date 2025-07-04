from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.auth import login as logout
from django.contrib.auth import login as dj_login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.db.models import Q
from ..forms import RegistrationForm
from ..forms import NachrichtenForm
from ..models import Nachrichten
from ..models import Profilbild

from ..utils import anz_neue_nachrichten, get_populated_nannys, get_relevant_nannys, paginate_list
from ..utils import send_new_message_email

index_site = 'web:index'

def logout_view(request):
    logout(request, request.user)
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
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.username = user.email
        user.save()
        # finally save the object in db
        group, created = Group.objects.get_or_create(pk=group_id)
        group.user_set.add(user)
        group.save()
        dj_login(request, user)
        if(group_id == 1):
            return redirect('web:create-profil')
        elif(group_id == 4):
            return redirect('web:create-profil-eltern')
        else:
            return redirect(index_site)
    context = {
        "form": form
    }
    return render(request, 'web/user.html', context)


def nachrichten(request, empfaenger_id=None):
    current_user = request.user
    if request.method == 'GET' and request.GET.get('delete') == 'True' and empfaenger_id is not None:
        empfaenger = User.objects.get(pk=int(empfaenger_id))
        Nachrichten.objects.filter(Q(sender=current_user, empfaenger=empfaenger)| Q(
            sender=empfaenger, empfaenger=current_user)).delete()
        return redirect('web:nachrichten')
    form = NachrichtenForm(request.POST or None)
    # getting other user
    empfaenger = None
    pb = None
    if empfaenger_id is not None:
        empfaenger = User.objects.get(pk=int(empfaenger_id))
        pb = Profilbild.objects.get(user=empfaenger)
    # messages of the conversation

    meldungen = list(Nachrichten.objects.filter(Q(
        sender=current_user, empfaenger=empfaenger)| Q(
        empfaenger=current_user, sender=empfaenger)).order_by('created'))
    for meldung in meldungen:
        if meldung.empfaenger == current_user:
            meldung.gelesen = True
            meldung.save()
    meldungen.sort(key=lambda x: x.created)
    # last_messages
    senders = list(Nachrichten.objects.filter(empfaenger=current_user)
                   .values_list("sender", flat=True)
                   .distinct())
    recievers = list(Nachrichten.objects.filter(sender=current_user)
                     .values_list("empfaenger", flat=True)
                     .distinct())
    last_message = None
    list_of_interactions = []
    for sender in senders:
        messages = Nachrichten.objects.filter(
            empfaenger=current_user, sender=sender).order_by('-created')
        if(messages is not None and len(messages) > 0):
            last_sender_message = messages[0]
            last_message = last_sender_message
            if recievers.__contains__(sender):
                last_reciever_message = Nachrichten.objects.filter(
                    sender=current_user, empfaenger=sender).order_by('-created')[0]
                if last_sender_message.created > last_reciever_message.created:
                    last_message = last_sender_message
        list_of_interactions.append({
            'user': User.objects.get(pk=sender),
            'last_message': last_message,
            'new_messages': Nachrichten.objects.filter(empfaenger=current_user, sender=sender, gelesen=False).count(),
            'bild': Profilbild.objects.get(user=sender)
        })
    for reciever in recievers:
        messages = Nachrichten.objects.filter(
            empfaenger=reciever, sender=current_user).order_by('-created')
        if(messages is not None and len(messages) > 0):
            last_reciever_message = messages[0]
            last_message = last_reciever_message
            if senders.__contains__(reciever):
                last_sender_message = Nachrichten.objects.filter(
                    sender=current_user, empfaenger=reciever).order_by('-created')[0]
                if last_sender_message.created > last_reciever_message.created:
                    last_message = last_sender_message
        list_of_interactions.append({
            'user': User.objects.get(pk=reciever),
            'last_message': last_message,
            'new_messages': 0,
            'bild': Profilbild.objects.get(user=reciever)
        })
    list_of_interactions = sorted(
        list_of_interactions, key=lambda k: k['last_message'].created)
    list_of_interactions = list(
        {v['user']: v for v in list_of_interactions}.values())
    list_of_interactions = sorted(
        list_of_interactions, key=lambda k: k['last_message'].created, reverse=True)

    group = request.user.groups.values_list('name', flat=True)[0]

    if request.method == 'POST':
        form = NachrichtenForm(request.POST)

        if form.is_valid():
            # process form data
            nachrichten = Nachrichten()
            nachrichten.sender = request.user
            nachrichten.empfaenger = empfaenger
            nachrichten.meldung = form.cleaned_data['meldung']
            nachrichten.created = timezone.now()
            nachrichten.gelesen = False
            # finally save the object in db
            nachrichten.save()
            send_new_message_email(empfaenger, request.user)
            return redirect(request.get_full_path_info(), empfaenger_id=empfaenger_id)
    context = {
        "form": form,
        "meldungen": meldungen,
        "empfaenger_id": empfaenger_id,
        "empfaenger": empfaenger,
        "bild": pb,
        'pbMe': Profilbild.objects.get(user=current_user),
        "list_of_interactions": list_of_interactions,
        "group": group,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/nachrichten.html', context)


def delete_user(request):
    request.user.delete()
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
        group = self.request.user.groups.values_list('name', flat=True)[0]
        context = super(SettingsView, self).get_context_data(**kwargs)
        context['user'] = currentuser
        context['group'] =  group
        return context
