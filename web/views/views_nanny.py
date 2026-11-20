from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from ..forms import (
    AdditionalSkillsChildForm,
    AngabejobForm,
    DescriptionForm,
    ExperiencechildForm,
    ProfilForm,
    ProfilbildForm,
    UserAccountForm,
)
from ..models import (
    AdditionalSkillsChild,
    Angabejob,
    Description,
    Experiencechild,
    Profil,
    Profilbild,
    Profileltern,
)
from ..utils import (
    anz_neue_nachrichten,
    create_profileimage,
    get_populated_parents,
    get_relevant_parents,
    paginate_list,
    send_new_user_email_jobsearch,
)


def _get_nanny_profile_or_404(user):
    profil = Profil.objects.filter(user=user).first()
    if not profil:
        raise Http404()
    return profil


@login_required
@require_http_methods(["GET", "POST"])
def create_profil(request):
    profil = Profil.objects.filter(user=request.user).first()
    form = ProfilForm(request.POST or None, instance=profil)
    if request.method == 'POST' and form.is_valid():
        profil = form.save(commit=False)
        profil.user = request.user
        profil.save()
        return redirect('web:angabejob')
    return render(request, 'web/nanny/profil.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def createangabejob(request):
    _get_nanny_profile_or_404(request.user)
    angabejob = Angabejob.objects.filter(user=request.user).first()
    form = AngabejobForm(request.POST or None, instance=angabejob)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect('web:create-description')
    return render(request, 'web/nanny/angabejob.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def create_description(request):
    _get_nanny_profile_or_404(request.user)
    description = Description.objects.filter(user=request.user).first()
    form = DescriptionForm(request.POST or None, instance=description)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect('web:experiencechild')
    return render(request, 'web/nanny/description.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def experiencechild(request):
    _get_nanny_profile_or_404(request.user)
    obj = Experiencechild.objects.filter(user=request.user).first()
    form = ExperiencechildForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:additionalskillschild')
    return render(request, 'web/nanny/experiencechild.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def additionalskillschild(request):
    _get_nanny_profile_or_404(request.user)
    obj = AdditionalSkillsChild.objects.filter(user=request.user).first()
    form = AdditionalSkillsChildForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        inst = form.save(commit=False)
        inst.user = request.user
        inst.save()
        return redirect('web:dateinanny')
    return render(request, 'web/nanny/additionalskillschild.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def dateinanny(request):
    _get_nanny_profile_or_404(request.user)
    if request.method == "POST":
        form = ProfilbildForm(request.POST, request.FILES)
        if form.is_valid():
            create_profileimage(request, form)
            # ensure dependent records exist with safe defaults
            Angabejob.objects.get_or_create(user=request.user)
            Description.objects.get_or_create(user=request.user)
            Experiencechild.objects.get_or_create(user=request.user)
            AdditionalSkillsChild.objects.get_or_create(user=request.user)
            send_new_user_email_jobsearch(request.user)
            return redirect('web:startseitenanny')
    else:
        form = ProfilbildForm()
    return render(request, "web/nanny/Datei.html", {'form': form})


def profil_nanny(request, user_id=None):
    viewer = request.user if request.user.is_authenticated else None
    if user_id is None:
        if not viewer or not viewer.is_authenticated:
            return redirect('login')
        target = viewer
        is_owner = True
    else:
        target = get_object_or_404(User, pk=user_id, groups__name='Nanny', is_active=True)
        is_owner = bool(viewer and viewer.pk == target.pk)

    profil = get_object_or_404(Profil, user=target)
    if not profil.is_public and not is_owner:
        raise Http404()

    description = Description.objects.filter(user=target).first()
    experiencechild = Experiencechild.objects.filter(user=target).first()
    additionalskillschild = AdditionalSkillsChild.objects.filter(user=target).first()
    profilbild = Profilbild.objects.filter(user=target).first() or Profilbild(user=target)
    angabejob = Angabejob.objects.filter(user=target).first()

    if not all([description, experiencechild, additionalskillschild, angabejob]):
        if is_owner:
            messages.info(request, 'Bitte vervollständigen Sie Ihr Profil.')
            return redirect('web:create-profil')
        raise Http404()

    context = {
        'user': target,
        'profil': profil,
        'description': description,
        'experiencechild': experiencechild,
        'profilbild': profilbild,
        'additionalskillschild': additionalskillschild,
        'angabejob': angabejob,
        'nanny': is_owner,
        'is_owner': is_owner,
        'anz_neue_nachrichten': anz_neue_nachrichten(request) if viewer else 0,
    }
    return render(request, 'web/Nanny.Login/profil-nanny-view.html', context)


@login_required
def startseitenanny(request):
    if not request.user.groups.filter(name='Nanny').exists():
        raise Http404()
    currentuser = request.user
    profilnanny = _get_nanny_profile_or_404(currentuser)
    term = request.POST.get('term') if request.method == 'POST' else None

    eltern_qs = get_relevant_parents(request, public_only=True, fallback_profile=profilnanny)
    if (term is None or term == '') and not request.method == 'POST':
        term = profilnanny.ort

    page_range, page_obj = paginate_list(request, eltern_qs, 15)
    eltern = get_populated_parents(page_obj.object_list, for_owner_ids=set(), include_private_fields=False)
    # rewrap page object content
    page_obj.object_list = eltern

    context = {
        'user': currentuser,
        'profil': profilnanny,
        'description': Description.objects.filter(user=currentuser).first(),
        'profilbild': Profilbild.objects.filter(user=currentuser).first() or Profilbild(user=currentuser),
        'eltern': page_obj,
        'range': page_range,
        'suchterm': term or '',
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    }
    return render(request, 'web/Nanny.Login/Startseite-nanny.html', context)


@login_required
def premiumnanny(request):
    if not request.user.groups.filter(name='Nanny').exists():
        raise Http404()
    return render(request, 'web/Nanny.Login/premium.html', {
        'user': request.user,
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    })


@login_required
@require_http_methods(["GET", "POST"])
def bearbeitungnanny(request):
    if not request.user.groups.filter(name='Nanny').exists():
        raise Http404()
    currentuser = request.user
    profil = _get_nanny_profile_or_404(currentuser)
    description, _ = Description.objects.get_or_create(user=currentuser)
    angabejob, _ = Angabejob.objects.get_or_create(user=currentuser)
    experiencechild, _ = Experiencechild.objects.get_or_create(user=currentuser)
    additional_skills_child, _ = AdditionalSkillsChild.objects.get_or_create(user=currentuser)
    bild = Profilbild.objects.filter(user=currentuser).first() or Profilbild(user=currentuser)

    user_form = UserAccountForm(instance=currentuser)
    profil_form = ProfilForm(instance=profil)
    description_form = DescriptionForm(instance=description)
    angabe_job_form = AngabejobForm(instance=angabejob)
    experience_child_form = ExperiencechildForm(instance=experiencechild)
    additional_skills_child_form = AdditionalSkillsChildForm(instance=additional_skills_child)
    image_form = ProfilbildForm()

    if request.method == 'POST':
        if 'image_upload' in request.POST:
            image_form = ProfilbildForm(request.POST, request.FILES)
            if image_form.is_valid():
                create_profileimage(request, image_form)
                messages.success(request, 'Profilbild aktualisiert.')
                return redirect('web:bearbeitungnanny')
        elif 'userdata_save' in request.POST:
            user_form = UserAccountForm(request.POST, instance=currentuser)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                email = user_form.cleaned_data['email'].lower().strip()
                user.email = email
                user.username = email
                user.save()
                messages.success(request, 'Kontodaten aktualisiert.')
                return redirect('web:bearbeitungnanny')
        elif 'place_save' in request.POST or 'profiltier' in request.POST:
            profil_form = ProfilForm(request.POST, instance=profil)
            if profil_form.is_valid():
                profil_form.save()
                messages.success(request, 'Profildaten aktualisiert.')
                return redirect('web:bearbeitungnanny')
        elif 'angabejob_save' in request.POST:
            angabe_job_form = AngabejobForm(request.POST, instance=angabejob)
            if angabe_job_form.is_valid():
                angabe_job_form.save()
                messages.success(request, 'Angaben aktualisiert.')
                return redirect('web:bearbeitungnanny')
        elif 'description_save' in request.POST:
            description_form = DescriptionForm(request.POST, instance=description)
            if description_form.is_valid():
                description_form.save()
                messages.success(request, 'Beschreibung aktualisiert.')
                return redirect('web:bearbeitungnanny')
        elif 'experience_save' in request.POST:
            experience_child_form = ExperiencechildForm(request.POST, instance=experiencechild)
            if experience_child_form.is_valid():
                experience_child_form.save()
                messages.success(request, 'Erfahrung aktualisiert.')
                return redirect('web:bearbeitungnanny')
        elif 'skills_save' in request.POST:
            additional_skills_child_form = AdditionalSkillsChildForm(request.POST, instance=additional_skills_child)
            if additional_skills_child_form.is_valid():
                additional_skills_child_form.save()
                messages.success(request, 'Skills aktualisiert.')
                return redirect('web:bearbeitungnanny')

    context = {
        'user': currentuser,
        'bild': bild,
        'userForm': user_form,
        'profilForm': profil_form,
        'descriptionForm': description_form,
        'experiencechildForm': experience_child_form,
        'additionalskillschildForm': additional_skills_child_form,
        'angabejobForm': angabe_job_form,
        'imageForm': image_form,
        'anz_neue_nachrichten': anz_neue_nachrichten(request),
    }
    return render(request, 'web/Nanny.Login/bearbeitungnanny.html', context)
