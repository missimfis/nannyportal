from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User

from ..forms import ProfilelternForm
from ..forms import JobangebotForm
from ..forms import AnzahlkinderForm
from ..forms import AnfoderungelternForm
from ..forms import BetreuungsZeitElternForm
from ..forms import DescriptionelternForm
from ..forms import ProfilbildForm
from ..forms import UserForm

from ..models import Profileltern
from ..models import Jobangebot
from ..models import Anzahlkinder
from ..models import Anfoderungeltern
from ..models import BetreuungsZeitEltern
from ..models import Descriptioneltern
from ..models import Profilbild

from ..utils import anz_neue_nachrichten
from ..utils import get_populated_nannys
from ..utils import paginate_list
from ..utils import get_relevant_nannys
from ..utils import create_profileimage
from ..utils import create_and_return_point2
# ELTERNINSERAT


def create_profil_eltern(request):
    profil = Profileltern.objects.filter(user=request.user).first()
    form = ProfilelternForm(request.POST or None, instance=profil)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if profil is None:
            profil = Profileltern()
        profil.user = request.user
        profil.plz = form.cleaned_data['plz']
        profil.ort = form.cleaned_data['ort']
        # finally save the object in db
        profil.save()
        create_and_return_point2(profil)
        return redirect('web:anzahl-kinder')
    context = {
        "form": form
    }

    return render(request, 'web/Eltern/Ort-Eltern.html', context)


def jobangebot(request):
    jobangebot = Jobangebot.objects.filter(user=request.user).first()
    form = JobangebotForm(request.POST or None, instance=jobangebot)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if jobangebot is None:
            jobangebot = Jobangebot()
        jobangebot.user = request.user
        jobangebot.nanny = form.cleaned_data['nanny']
        jobangebot.tagesmutter = form.cleaned_data['tagesmutter']

        # finally save the object in db
        jobangebot.save()
        return redirect('web:anzahl-kinder')

    context = {
        "form": form
    }

    return render(request, 'web/Eltern/Jobangebot.html', context)


def anzahlkinder(request):
    anzahlkinder = Anzahlkinder.objects.filter(user=request.user).first()
    form = AnzahlkinderForm(request.POST or None, instance=anzahlkinder)
    if request.method == 'POST' and form.is_valid():
        # process form data
        anzahlkinder = Anzahlkinder()
        anzahlkinder.user = request.user
        anzahlkinder.ein_kind = form.cleaned_data['ein_kind']
        anzahlkinder.zwei_kinder = form.cleaned_data['zwei_kinder']
        anzahlkinder.drei_kinder = form.cleaned_data['drei_kinder']
        anzahlkinder.vier_plus_kinder = form.cleaned_data['vier_plus_kinder']
        anzahlkinder.neugeborenes_baby = form.cleaned_data['neugeborenes_baby']
        anzahlkinder.kleinkind = form.cleaned_data['kleinkind']
        anzahlkinder.kindergartenalter = form.cleaned_data['kindergartenalter']
        anzahlkinder.schulalter = form.cleaned_data['schulalter']
        anzahlkinder.teenager = form.cleaned_data['teenager']

        # finally save the object in db
        anzahlkinder.save()
        return redirect('web:anfoderungeltern')

    context = {
        "form": form
    }

    return render(request, 'web/Eltern/Anzahl-Kinder.html', context)


def anfoderungeltern(request):
    anfoderungeltern = Anfoderungeltern.objects.filter(user=request.user).first()
    form = AnfoderungelternForm(
        request.POST or None, instance=anfoderungeltern)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if anfoderungeltern is None:
            anfoderungeltern = Anfoderungeltern()
        anfoderungeltern.user = request.user
        anfoderungeltern.essenzubereitung = form.cleaned_data['essenzubereitung']
        anfoderungeltern.unterstutzung_bei_hausaufgaben = form.cleaned_data[
            'unterstutzung_bei_hausaufgaben']
        anfoderungeltern.bring_und_abholung = form.cleaned_data['bring_und_abholung']
        anfoderungeltern.leichte_haushaltarbeiten = form.cleaned_data[
            'leichte_haushaltarbeiten']
        anfoderungeltern.kind_fodern_beim_Sprechen = form.cleaned_data[
            'kind_fodern_beim_Sprechen']

        # finally save the object in db
        anfoderungeltern.save()
        return redirect('web:descriptioneltern')

    context = {
        "form": form
    }

    return render(request, 'web/Eltern/Anfoderung_eltern.html', context)


def descriptioneltern(request):
    descriptioneltern = Descriptioneltern.objects.filter(user=request.user).first()
    form = DescriptionelternForm(
        request.POST or None, instance=descriptioneltern)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if descriptioneltern is None:
            descriptioneltern = Descriptioneltern()
        descriptioneltern.user = request.user
        descriptioneltern.description = form.cleaned_data['description']
        # finally save the object in db
        descriptioneltern.save()
        return redirect('web:betreuungszeiteltern')

    context = {
        "form": form
    }

    return render(request, 'web/Eltern/descriptioneltern.html', context)


def betreuungszeiteltern(request):
    betreuungszeiteltern = BetreuungsZeitEltern.objects.filter(
            user=request.user).first()
    form = BetreuungsZeitElternForm(
        request.POST or None, instance=betreuungszeiteltern)
    if request.method == 'POST' and form.is_valid():
        if betreuungszeiteltern is None:
            betreuungszeiteltern = BetreuungsZeitEltern()
        betreuungszeiteltern.user = request.user

        betreuungszeiteltern.Mo_Vor = form.cleaned_data['Mo_Vor']
        betreuungszeiteltern.Di_Vor = form.cleaned_data['Di_Vor']
        betreuungszeiteltern.Mi_Vor = form.cleaned_data['Mi_Vor']
        betreuungszeiteltern.Do_Vor = form.cleaned_data['Do_Vor']
        betreuungszeiteltern.Fr_Vor = form.cleaned_data['Fr_Vor']
        betreuungszeiteltern.Sa_Vor = form.cleaned_data['Sa_Vor']
        betreuungszeiteltern.So_Vor = form.cleaned_data['So_Vor']

        betreuungszeiteltern.Mo_Nach = form.cleaned_data['Mo_Nach']
        betreuungszeiteltern.Di_Nach = form.cleaned_data['Di_Nach']
        betreuungszeiteltern.Mi_Nach = form.cleaned_data['Mi_Nach']
        betreuungszeiteltern.Do_Nach = form.cleaned_data['Do_Nach']
        betreuungszeiteltern.Fr_Nach = form.cleaned_data['Fr_Nach']
        betreuungszeiteltern.Sa_Nach = form.cleaned_data['Sa_Nach']
        betreuungszeiteltern.So_Nach = form.cleaned_data['So_Nach']

        betreuungszeiteltern.Mo_Ab = form.cleaned_data['Mo_Ab']
        betreuungszeiteltern.Di_Ab = form.cleaned_data['Di_Ab']
        betreuungszeiteltern.Mi_Ab = form.cleaned_data['Mi_Ab']
        betreuungszeiteltern.Do_Ab = form.cleaned_data['Do_Ab']
        betreuungszeiteltern.Fr_Ab = form.cleaned_data['Fr_Ab']
        betreuungszeiteltern.Sa_Ab = form.cleaned_data['Sa_Ab']
        betreuungszeiteltern.So_Ab = form.cleaned_data['So_Ab']

        betreuungszeiteltern.Mo_uberna = form.cleaned_data['Mo_uberna']
        betreuungszeiteltern.Di_uberna = form.cleaned_data['Di_uberna']
        betreuungszeiteltern.Mi_uberna = form.cleaned_data['Mi_uberna']
        betreuungszeiteltern.Do_uberna = form.cleaned_data['Do_uberna']
        betreuungszeiteltern.Fr_uberna = form.cleaned_data['Fr_uberna']
        betreuungszeiteltern.Sa_uberna = form.cleaned_data['Sa_uberna']
        betreuungszeiteltern.So_uberna = form.cleaned_data['So_uberna']

        betreuungszeiteltern.save()
        return redirect('web:datei')

    context = {
        "form": form
    }

    return render(request, 'web/Eltern/Betreuungszeit.html', context)


def datei(request):
    if request.method == "POST":
        form = ProfilbildForm(request.POST, request.FILES)
        if form.is_valid():
            create_profileimage(request,form)
            return redirect('web:startseiteeltern')
    else:
        form = ProfilbildForm()
    context = {'form': form}
    return render(request, "web/Eltern/Datei.html", context)


def profileltern(request, user_id=None):
    if user_id is None:
        currentuser = request.user
        eltern = True
    else:
        currentuser = User.objects.get(pk=user_id)
        eltern = False
    profil = Profileltern.objects.get(user=currentuser)
    description = Descriptioneltern.objects.get(user=currentuser)
    anzahlkinder = Anzahlkinder.objects.get(user=currentuser)
    anforderungeneltern = Anfoderungeltern.objects.get(user=currentuser)
    betreuungszeiteltern = BetreuungsZeitEltern.objects.get(user=currentuser)
    profilbild = Profilbild.objects.get(user=currentuser)
    context = {
        'user': currentuser,
        'profil': profil,
        'profilbild': profilbild,
        'description': description,
        'anforderungeneltern': anforderungeneltern,
        'anzahlkinder': anzahlkinder,
        'betreuungszeiteltern': betreuungszeiteltern,
        'eltern': eltern,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/Eltern.Profilseite/Profil-Eltern.html', context)


def startseiteeltern(request):
    currentuser = request.user
    profileltern = Profileltern.objects.get(user=currentuser)
    term = None
    if request.POST is not None:
        term = request.POST.get('term')
    nannys = get_relevant_nannys(request)
    
    if term is None or term == '':
        term = profileltern.ort
    pagination = paginate_list(request, get_populated_nannys(nannys), 15)
    context = {
        'user': currentuser,
        'profil': profileltern,
        'description': Descriptioneltern.objects.get(user=currentuser),
        'nanny_list': pagination[1],
        'range': pagination[0],
        'profilbild': Profilbild.objects.get(user=currentuser),
        'suchterm': term,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/Eltern.Profilseite/Startseite-Eltern.html', context)

def schnuppern(request):
    term = request.POST.get('term','')
    nannys = get_relevant_nannys(request)

    pagination = paginate_list(request, get_populated_nannys(nannys), 15)
    context = {
        'nanny_list': pagination[1],
        'range': pagination[0],
        'suchterm': term
    }
    return render(request, 'web/schnuppern.html', context)


def premiumeltern(request):
    currentuser = request.user
    context = {
        'user': currentuser,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/Eltern.Profilseite/Premium-Eltern.html', context)


def bearbeitungelternprofil(request):
    currentuser = request.user
    profil = Profileltern.objects.get(user=currentuser)
    description = Descriptioneltern.objects.get(user=currentuser)
    anzahlkinder = Anzahlkinder.objects.get(user=currentuser)
    anforderungeneltern = Anfoderungeltern.objects.get(user=currentuser)
    betreuungszeiteltern = BetreuungsZeitEltern.objects.get(user=currentuser)

    if request.method == 'POST':
        if 'image_upload' in request.POST:
            form = ProfilbildForm(request.POST, request.FILES)
            if form.is_valid():
                create_profileimage(request, form)
        if 'userdata' in request.POST:
            user_form = UserForm(request.POST, instance=currentuser)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.username = user.email
                user.set_password(user.password)
                user.save()
        elif 'orteltern' in request.POST:
            profil_eltern_form = ProfilelternForm(
                request.POST, instance=profil)
            if profil_eltern_form.is_valid():
                profil = profil_eltern_form.save()
                create_and_return_point2(profil)
        elif 'texteltern' in request.POST:
            description_eltern_form = DescriptionelternForm(
                request.POST, instance=description)
            if description_eltern_form.is_valid():
                description_eltern_form.save()
        elif 'anzahlkinder' in request.POST:
            anzahl_kinder_form = AnzahlkinderForm(
                request.POST, instance=anzahlkinder)
            if anzahl_kinder_form.is_valid():
                anzahl_kinder_form.save()
        elif 'anfoderungeltern' in request.POST:
            anforderung_eltern_form = AnfoderungelternForm(
                request.POST, instance=anforderungeneltern)
            if anforderung_eltern_form.is_valid():
                anforderung_eltern_form.save()
        elif 'zeiteltern' in request.POST:
            betreuungszeit_eltern_form = BetreuungsZeitElternForm(
                request.POST, instance=betreuungszeiteltern)
            if betreuungszeit_eltern_form.is_valid():
                betreuungszeit_eltern_form.save()
        return redirect('web:profileltern')
    else:
        user_form = UserForm(instance=currentuser)
        profil_eltern_form = ProfilelternForm(instance=profil)
        description_eltern_form = DescriptionelternForm(instance=description)
        anzahl_kinder_form = AnzahlkinderForm(instance=anzahlkinder)
        anforderung_eltern_form = AnfoderungelternForm(
            instance=anforderungeneltern)
        betreuungszeit_eltern_form = BetreuungsZeitElternForm(
            instance=betreuungszeiteltern)

    context = {
        'user': currentuser,
        'userForm': user_form,
        'bild': Profilbild.objects.get(user=currentuser),
        'profilElternForm': profil_eltern_form,
        'descriptionElternForm': description_eltern_form,
        'anzahlKinderForm': anzahl_kinder_form,
        'anforderungElternForm': anforderung_eltern_form,
        'betreuungszeitElternForm': betreuungszeit_eltern_form
    }
    return render(request, 'web/Eltern.Profilseite/bearbeiteneltern.html', context)
