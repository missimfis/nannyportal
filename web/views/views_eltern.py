from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from ..forms import (
    AnfoderungelternForm,
    AnzahlkinderForm,
    BetreuungsZeitElternForm,
    DescriptionelternForm,
    JobangebotForm,
    ProfilelternForm,
    ProfilbildForm,
    UserAccountForm,
)
from ..models import (
    Anfoderungeltern,
    Anzahlkinder,
    BetreuungsZeitEltern,
    Descriptioneltern,
    Jobangebot,
    Profileltern,
    Profilbild,
)
from ..utils import (
    anz_neue_nachrichten,
    create_profileimage,
    get_populated_nannys,
    get_relevant_nannys,
    paginate_list,
)


def _get_parent_profile_or_404(user):
    profil = Profileltern.objects.filter(user=user).first()
    if not profil:
        raise Http404()
    return profil


@login_required
@require_http_methods(["GET", "POST"])
def create_profil_eltern(request):
    profil = Profileltern.objects.filter(user=request.user).first()
    form = ProfilelternForm(request.POST or None, instance=profil)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect('web:anzahl-kinder')
    return render(request, 'web/Eltern/Ort-Eltern.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def jobangebot(request):
    _get_parent_profile_or_404(request.user)
    obj = Jobangebot.objects.filter(user=request.user).first()
    form = JobangebotForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:anzahl-kinder')
    return render(request, 'web/Eltern/Jobangebot.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def anzahlkinder(request):
    _get_parent_profile_or_404(request.user)
    obj = Anzahlkinder.objects.filter(user=request.user).first()
    form = AnzahlkinderForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:anfoderungeltern')
    return render(request, 'web/Eltern/Anzahl-Kinder.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def anfoderungeltern(request):
    _get_parent_profile_or_404(request.user)
    obj = Anfoderungeltern.objects.filter(user=request.user).first()
    form = AnfoderungelternForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:descriptioneltern')
    return render(request, 'web/Eltern/Anfoderung_eltern.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def descriptioneltern(request):
    _get_parent_profile_or_404(request.user)
    obj = Descriptioneltern.objects.filter(user=request.user).first()
    form = DescriptionelternForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:betreuungszeiteltern')
    return render(request, 'web/Eltern/descriptioneltern.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def betreuungszeiteltern(request):
    _get_parent_profile_or_404(request.user)
    obj = BetreuungsZeitEltern.objects.filter(user=request.user).first()
    form = BetreuungsZeitElternForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:datei')
    return render(request, 'web/Eltern/Betreuungszeit.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def datei(request):
    _get_parent_profile_or_404(request.user)
    if request.method == "POST":
        form = ProfilbildForm(request.POST, request.FILES)
        if form.is_valid():
            create_profileimage(request, form)
            # ensure records exist
            Anzahlkinder.objects.get_or_create(user=request.user)
            Anfoderungeltern.objects.get_or_create(user=request.user)
            Descriptioneltern.objects.get_or_create(user=request.user)
            BetreuungsZeitEltern.objects.get_or_create(user=request.user)
            return redirect('web:startseiteeltern')
    else:
        form = ProfilbildForm()
    return render(request, "web/Eltern/Datei.html", {'form': form})


def profileltern(request, user_id=None):
    viewer = request.user if request.user.is_authenticated else None
    if user_id is None:
        if not viewer or not viewer.is_authenticated:
            return redirect('login')
        target = viewer
        is_owner = True
    else:
        target = get_object_or_404(User, pk=user_id, groups__name='Eltern', is_active=True)
        is_owner = bool(viewer and viewer.pk == target.pk)

    profil = get_object_or_404(Profileltern, user=target)
    if not profil.is_public and not is_owner:
        raise Http404()

    description = Descriptioneltern.objects.filter(user=target).first()
    anzahlkinder = Anzahlkinder.objects.filter(user=target).first()
    anforderungeneltern = Anfoderungeltern.objects.filter(user=target).first()
    betreuungszeiteltern = BetreuungsZeitEltern.objects.filter(user=target).first()
    profilbild = Profilbild.objects.filter(user=target).first() or Profilbild(user=target)

    if not all([description, anzahlkinder, anforderungeneltern, betreuungszeiteltern]):
        if is_owner:
            messages.info(request, 'Bitte vervollständigen Sie Ihr Profil.')
            return redirect('web:create-profil-eltern')
        raise Http404()

    context = {
        'user': target,
        'profil': profil,
        'profilbild': profilbild,
        'description': description,
        'anforderungeneltern': anforderungeneltern,
        'anzahlkinder': anzahlkinder,
        'betreuungszeiteltern': betreuungszeiteltern,
        'eltern': is_owner,
        'is_owner': is_owner,
        'anz_neue_nachrichten': anz_neue_nachrichten(request) if viewer else 0,
    }
    return render(request, 'web/Eltern.Profilseite/Profil-Eltern.html', context)


@login_required
def startseiteeltern(request):
    if not request.user.groups.filter(name='Eltern').exists():
        raise Http404()
    currentuser = request.user
    profileltern = _get_parent_profile_or_404(currentuser)
    term = request.POST.get('term') if request.method == 'POST' else None

    nannys_qs = get_relevant_nannys(request, public_only=True, fallback_profile=profileltern)
    if (term is None or term == '') and not request.method == 'POST':
        term = profileltern.ort

    page_range, page_obj = paginate_list(request, nannys_qs, 15)
    nanny_list = get_populated_nannys(page_obj.object_list, include_private_fields=False)
    page_obj.object_list = nanny_list

    context = {
        'user': currentuser,
        'profil': profileltern,
        'description': Descriptioneltern.objects.filter(user=currentuser).first(),
        'nanny_list': page_obj,
        'range': page_range,
        'profilbild': Profilbild.objects.filter(user=currentuser).first() or Profilbild(user=currentuser),
        'suchterm': term or '',
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    }
    return render(request, 'web/Eltern.Profilseite/Startseite-Eltern.html', context)


def schnuppern(request):
    term = request.POST.get('term', '')
    nannys_qs = get_relevant_nannys(request, public_only=True)
    page_range, page_obj = paginate_list(request, nannys_qs, 15)
    nanny_list = get_populated_nannys(page_obj.object_list, include_private_fields=False)
    page_obj.object_list = nanny_list
    return render(request, 'web/schnuppern.html', {
        'nanny_list': page_obj,
        'range': page_range,
        'suchterm': term,
    })


@login_required
def premiumeltern(request):
    if not request.user.groups.filter(name='Eltern').exists():
        raise Http404()
    return render(request, 'web/Eltern.Profilseite/Premium-Eltern.html', {
        'user': request.user,
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    })


@login_required
@require_http_methods(["GET", "POST"])
def bearbeitungelternprofil(request):
    if not request.user.groups.filter(name='Eltern').exists():
        raise Http404()
    currentuser = request.user
    profil = _get_parent_profile_or_404(currentuser)
    description, _ = Descriptioneltern.objects.get_or_create(user=currentuser)
    anzahlkinder, _ = Anzahlkinder.objects.get_or_create(user=currentuser)
    anforderungeneltern, _ = Anfoderungeltern.objects.get_or_create(user=currentuser)
    betreuungszeiteltern, _ = BetreuungsZeitEltern.objects.get_or_create(user=currentuser)
    bild = Profilbild.objects.filter(user=currentuser).first() or Profilbild(user=currentuser)

    user_form = UserAccountForm(instance=currentuser)
    profil_eltern_form = ProfilelternForm(instance=profil)
    description_eltern_form = DescriptionelternForm(instance=description)
    anzahl_kinder_form = AnzahlkinderForm(instance=anzahlkinder)
    anforderung_eltern_form = AnfoderungelternForm(instance=anforderungeneltern)
    betreuungszeit_eltern_form = BetreuungsZeitElternForm(instance=betreuungszeiteltern)
    image_form = ProfilbildForm()

    if request.method == 'POST':
        if 'image_upload' in request.POST:
            image_form = ProfilbildForm(request.POST, request.FILES)
            if image_form.is_valid():
                create_profileimage(request, image_form)
                messages.success(request, 'Profilbild aktualisiert.')
                return redirect('web:bearbeitungelternprofil')
        elif 'userdata' in request.POST:
            user_form = UserAccountForm(request.POST, instance=currentuser)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                email = user_form.cleaned_data['email'].lower().strip()
                user.email = email
                user.username = email
                user.save()
                messages.success(request, 'Kontodaten aktualisiert.')
                return redirect('web:bearbeitungelternprofil')
        elif 'orteltern' in request.POST:
            profil_eltern_form = ProfilelternForm(request.POST, instance=profil)
            if profil_eltern_form.is_valid():
                profil_eltern_form.save()
                messages.success(request, 'Profildaten aktualisiert.')
                return redirect('web:bearbeitungelternprofil')
        elif 'texteltern' in request.POST:
            description_eltern_form = DescriptionelternForm(request.POST, instance=description)
            if description_eltern_form.is_valid():
                description_eltern_form.save()
                messages.success(request, 'Beschreibung aktualisiert.')
                return redirect('web:bearbeitungelternprofil')
        elif 'anzahlkinder' in request.POST:
            anzahl_kinder_form = AnzahlkinderForm(request.POST, instance=anzahlkinder)
            if anzahl_kinder_form.is_valid():
                anzahl_kinder_form.save()
                messages.success(request, 'Angaben aktualisiert.')
                return redirect('web:bearbeitungelternprofil')
        elif 'anfoderungeltern' in request.POST:
            anforderung_eltern_form = AnfoderungelternForm(request.POST, instance=anforderungeneltern)
            if anforderung_eltern_form.is_valid():
                anforderung_eltern_form.save()
                messages.success(request, 'Angaben aktualisiert.')
                return redirect('web:bearbeitungelternprofil')
        elif 'zeiteltern' in request.POST:
            betreuungszeit_eltern_form = BetreuungsZeitElternForm(request.POST, instance=betreuungszeiteltern)
            if betreuungszeit_eltern_form.is_valid():
                betreuungszeit_eltern_form.save()
                messages.success(request, 'Zeiten aktualisiert.')
                return redirect('web:bearbeitungelternprofil')

    context = {
        'user': currentuser,
        'userForm': user_form,
        'bild': bild,
        'profilElternForm': profil_eltern_form,
        'descriptionElternForm': description_eltern_form,
        'anzahlKinderForm': anzahl_kinder_form,
        'anforderungElternForm': anforderung_eltern_form,
        'betreuungszeitElternForm': betreuungszeit_eltern_form,
        'imageForm': image_form,
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    }
    return render(request, 'web/Eltern.Profilseite/bearbeiteneltern.html', context)
