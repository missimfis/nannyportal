from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User

from ..forms import ProfilForm
from ..forms import AngabejobForm
from ..forms import DescriptionForm
from ..forms import ExperiencechildForm
from ..forms import AdditionalSkillsChildForm
from ..forms import ProfilbildForm
from ..forms import UserForm

from ..models import Profil
from ..models import Angabejob
from ..models import Description
from ..models import Experiencechild
from ..models import AdditionalSkillsChild
from ..models import Profilbild
from ..models import Profileltern
from ..models import Descriptioneltern
from ..models import BetreuungsZeitEltern

from ..utils import anz_neue_nachrichten
from ..utils import send_new_user_email_jobsearch
from ..utils import paginate_list
from ..utils import create_and_return_point2
from ..utils import create_profileimage
from ..utils import get_populated_parents
from ..utils import get_relevant_parents
# Nanny Inserat


def create_profil(request):
    profil = Profil.objects.filter(user=request.user).first()
    form = ProfilForm(request.POST or None, instance=profil)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if profil is None:
            profil = Profil()
        profil.user = request.user
        profil.plz = form.cleaned_data['plz']
        profil.ort = form.cleaned_data['ort']
        profil.birth_date = form.cleaned_data['birth_date']
        profil.salary = form.cleaned_data['salary']

        # finally save the object in db
        profil.save()
        create_and_return_point2(profil)
        return redirect('web:angabejob')
    context = {
        "form": form
    }

    return render(request, 'web/nanny/profil.html', context)


def createangabejob(request):
    angabejob = Angabejob.objects.filter(user=request.user).first()
    form = AngabejobForm(request.POST or None, instance=angabejob)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if angabejob is None:
            angabejob = Angabejob()
        angabejob.user = request.user
        angabejob.angabe_job_nanny = form.cleaned_data['angabe_job_nanny']
        angabejob.angabe_job_tagesmutter = form.cleaned_data['angabe_job_tagesmutter']

        # finally save the object in db
        angabejob.save()
        return redirect('web:create-description')

    context = {
        "form": form
    }
    return render(request, 'web/nanny/angabejob.html', context)


def create_description(request):
    description = Description.objects.filter(user=request.user).first()
    form = DescriptionForm(request.POST or None, instance=description)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if description is None:
            description = Description()
        description.user = request.user
        description.description = form.cleaned_data['description']
        # finally save the object in db
        description.save()
        return redirect('web:experiencechild')

    context = {
        "form": form
    }

    return render(request, 'web/nanny/description.html', context)


def experiencechild(request):
    experiencechild = Experiencechild.objects.filter(user=request.user).first()
    form = ExperiencechildForm(request.POST or None, instance=experiencechild)
    if request.method == 'POST' and form.is_valid():
        # process form data
        if experiencechild is None:
            experiencechild = Experiencechild()
        experiencechild.user = request.user
        experiencechild.newborn_child_experience = form.cleaned_data['newborn_child_experience']
        experiencechild.infants_child_experience = form.cleaned_data['infants_child_experience']
        experiencechild.kindergarden_school_child_experience = form.cleaned_data[
            'kindergarden_school_child_experience']

        # finally save the object in db
        experiencechild.save()
        return redirect('web:additionalskillschild')

    context = {
        "form": form
    }

    return render(request, 'web/nanny/experiencechild.html', context)


def additionalskillschild(request):
    additionalskillschild = AdditionalSkillsChild.objects.filter(
        user=request.user).first()
    form = AdditionalSkillsChildForm(
        request.POST or None, instance=additionalskillschild)
    if request.method == 'POST' and form.is_valid():
        # process form data
        additionalskillschild = AdditionalSkillsChild()
        additionalskillschild.user = request.user
        additionalskillschild.fachfrau_course = form.cleaned_data['fachfrau_course']
        additionalskillschild.sitting_course = form.cleaned_data['sitting_course']
        additionalskillschild.drivers_licence = form.cleaned_data['drivers_licence']
        additionalskillschild.study = form.cleaned_data['study']
        additionalskillschild.ausbildung = form.cleaned_data['ausbildung']
        additionalskillschild.praktikum = form.cleaned_data['praktikum']
        additionalskillschild.arbeitserfahrung = form.cleaned_data['arbeitserfahrung']

        # finally save the object in db
        additionalskillschild.save()
        return redirect('web:dateinanny')

    context = {
        "form": form
    }

    return render(request, 'web/nanny/additionalskillschild.html', context)


def dateinanny(request):
    if request.method == "POST":
        form = ProfilbildForm(request.POST, request.FILES)
        if form.is_valid():
            create_profileimage(request, form)
            send_new_user_email_jobsearch(request.user)
            return redirect('web:startseitenanny')
    else:
        form = ProfilbildForm()
    context = {'form': form}
    return render(request, "web/nanny/Datei.html", context)


def profil_nanny(request, user_id=None):
    if user_id == None:
        currentuser = request.user
        nanny = True
    else:
        currentuser = User.objects.get(pk=user_id)
        nanny = False
    profil = Profil.objects.get(user=currentuser)
    description = Description.objects.get(user=currentuser)
    experiencechild = Experiencechild.objects.get(user=currentuser)
    additionalskillschild = AdditionalSkillsChild.objects.get(user=currentuser)
    profilbild = Profilbild.objects.get(user=currentuser)

    angabejob = Angabejob.objects.get(user=currentuser)
    context = {
        'user': currentuser,
        'profil': profil,
        'description': description,
        'experiencechild': experiencechild,
        'profilbild': profilbild,
        'additionalskillschild': additionalskillschild,
        'angabejob': angabejob,
        'nanny': nanny,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/Nanny.Login/profil-nanny-view.html', context)


def startseitenanny(request):
    currentuser = request.user
    profilnanny = Profil.objects.get(user=currentuser)
    term = request.POST.get('term') if request.method == 'POST' else None
    eltern = get_relevant_parents(request)

    if term is None or term == '':
        term = profilnanny.ort
    pagination = paginate_list(request, get_populated_parents(eltern), 15)
    context = {
        'user': currentuser,
        'profil': profilnanny,
        'description': Description.objects.get(user=currentuser),
        'profilbild': Profilbild.objects.get(user=currentuser),
        'eltern': pagination[1],
        'range': pagination[0],
        'suchterm': term,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/Nanny.Login/Startseite-nanny.html', context)


def premiumnanny(request):
    currentuser = request.user
    context = {
        'user': currentuser,
        'anz_neue_nachrichten': anz_neue_nachrichten(request)
    }
    return render(request, 'web/Nanny.Login/premium.html', context)


def bearbeitungnanny(request):
    currentuser = request.user
    profil = Profil.objects.get(user=currentuser)
    description = Description.objects.get(user=currentuser)
    angabejob = Angabejob.objects.get(user=currentuser)
    experiencechild = Experiencechild.objects.get(user=currentuser)
    additional_skills_child = AdditionalSkillsChild.objects.get(user=currentuser)

    if request.method == 'POST':
        if 'image_upload' in request.POST:
            form = ProfilbildForm(request.POST, request.FILES)
            if form.is_valid():
                create_profileimage(request, form)
        if 'userdata_save' in request.POST:
            user_form = UserForm(request.POST, instance=currentuser)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.username = user.email
                user.set_password(user.password)
                user.save()
        elif 'place_save' in request.POST:
            profil_form = ProfilForm(request.POST, instance=profil)
            if profil_form.is_valid():
                profil = profil_form.save()
                create_and_return_point2(profil)
        elif 'angabejob_save' in request.POST:
            angabe_job_form = AngabejobForm(
                request.POST, instance=angabejob)
            if angabe_job_form.is_valid():
                angabe_job_form.save()
        elif 'description_save' in request.POST:
            description_form = DescriptionForm(
                request.POST, instance=description)
            if description_form.is_valid():
                description_form.save()
        elif 'experience_save' in request.POST:
            experience_child_form = ExperiencechildForm(
                request.POST, instance=experiencechild)
            if experience_child_form.is_valid():
                experience_child_form.save()
        elif 'skills_save' in request.POST:
            additional_skills_child_form = AdditionalSkillsChildForm(
                request.POST, instance=additional_skills_child)
            if additional_skills_child_form.is_valid():
                additional_skills_child_form.save()
        return redirect('web:profilnanny')
    else:
        user_form = UserForm(instance=currentuser)
        profil_form = ProfilForm(instance=profil)
        description_form = DescriptionForm(instance=description)
        angabe_job_form = AngabejobForm(instance=angabejob)
        experience_child_form = ExperiencechildForm(instance=experiencechild)
        additional_skills_child_form = AdditionalSkillsChildForm(
            instance=additional_skills_child)

    context = {
        'user': currentuser,
        'bild': Profilbild.objects.get(user=currentuser),
        'userForm': user_form,
        'profilForm': profil_form,
        'descriptionForm': description_form,
        'experiencechildForm': experience_child_form,
        'additionalskillschildForm': additional_skills_child_form,
        'angabejobForm': angabe_job_form
    }
    return render(request, 'web/Nanny.Login/bearbeitungnanny.html', context)
