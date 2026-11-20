from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

from .image_utils import process_profile_image
from .models import (
    Anfoderungeltern, Angabejob, BetreuungsZeitEltern, Nachrichten,
    Profil, Description, Experiencechild, AdditionalSkillsChild,
    Profilbild, Profileltern, Anzahlkinder, Descriptioneltern, Jobangebot,
)

hidden_css = 'hidden css-eingeben'


# --- Nanny forms ---

class ProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        YEARS = [x for x in range(1955, 2021)]
        fields = ['plz', 'ort', 'salary', 'birth_date', 'is_public']
        labels = {
            'is_public': 'Profil in der Suche anzeigen',
        }
        widgets = {
            'plz': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'PLZ'}),
            'ort': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ort'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control profiltierbetreuer', 'placeholder': 'Gewünschter Stundenlohn'}),
            'birth_date': forms.SelectDateWidget(years=YEARS, attrs={'class': 'form-select datum'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AngabejobForm(forms.ModelForm):
    class Meta:
        model = Angabejob
        fields = ['angabe_job_nanny', 'angabe_job_tagesmutter']
        widgets = {
            'angabe_job_nanny': forms.CheckboxInput(attrs={'class': hidden_css}),
            'angabe_job_tagesmutter': forms.CheckboxInput(attrs={'class': hidden_css}),
        }


class UserAccountForm(forms.ModelForm):
    """Edit basic account identity fields only. Never handle passwords here."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nachname'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-Mail'}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('E-Mail ist erforderlich.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Diese E-Mail-Adresse ist bereits vergeben.')
        return email


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password1', 'password2']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nachname'}),
            'username': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-Mail'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        username = (self.cleaned_data.get("username") or '').strip().lower()
        user.username = username
        user.email = username
        if commit:
            user.save()
        return user


class DescriptionForm(forms.ModelForm):
    class Meta:
        model = Description
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Beschreiben Sie sich und Ihre Erfahrung...'}),
        }


class ExperiencechildForm(forms.ModelForm):
    class Meta:
        model = Experiencechild
        fields = ['newborn_child_experience', 'infants_child_experience', 'kindergarden_school_child_experience']
        widgets = {
            'newborn_child_experience': forms.CheckboxInput(attrs={'class': hidden_css}),
            'infants_child_experience': forms.CheckboxInput(attrs={'class': hidden_css}),
            'kindergarden_school_child_experience': forms.CheckboxInput(attrs={'class': hidden_css}),
        }


class AdditionalSkillsChildForm(forms.ModelForm):
    class Meta:
        model = AdditionalSkillsChild
        fields = ['fachfrau_course', 'sitting_course', 'drivers_licence', 'study', 'ausbildung', 'praktikum', 'arbeitserfahrung']
        widgets = {
            'fachfrau_course': forms.CheckboxInput(attrs={'class': hidden_css}),
            'sitting_course': forms.CheckboxInput(attrs={'class': hidden_css}),
            'drivers_licence': forms.CheckboxInput(attrs={'class': hidden_css}),
            'study': forms.CheckboxInput(attrs={'class': hidden_css}),
            'ausbildung': forms.CheckboxInput(attrs={'class': hidden_css}),
            'praktikum': forms.CheckboxInput(attrs={'class': hidden_css}),
            'arbeitserfahrung': forms.CheckboxInput(attrs={'class': hidden_css}),
        }


# --- Eltern forms ---

class ProfilelternForm(forms.ModelForm):
    class Meta:
        model = Profileltern
        fields = ['plz', 'ort', 'is_public']
        labels = {'is_public': 'Profil in der Suche anzeigen'}
        widgets = {
            'plz': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'PLZ'}),
            'ort': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ort'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class JobangebotForm(forms.ModelForm):
    class Meta:
        model = Jobangebot
        fields = ['nanny', 'tagesmutter']
        widgets = {
            'nanny': forms.CheckboxInput(attrs={'class': hidden_css}),
            'tagesmutter': forms.CheckboxInput(attrs={'class': hidden_css}),
        }


class AnzahlkinderForm(forms.ModelForm):
    class Meta:
        model = Anzahlkinder
        fields = ['ein_kind', 'zwei_kinder', 'drei_kinder', 'vier_plus_kinder',
                  'neugeborenes_baby', 'kleinkind', 'kindergartenalter', 'schulalter', 'teenager']
        widgets = {f: forms.CheckboxInput(attrs={'class': hidden_css}) for f in fields}


class AnfoderungelternForm(forms.ModelForm):
    class Meta:
        model = Anfoderungeltern
        fields = ['essenzubereitung', 'unterstutzung_bei_hausaufgaben',
                  'bring_und_abholung', 'leichte_haushaltarbeiten', 'kind_fodern_beim_Sprechen']
        widgets = {f: forms.CheckboxInput(attrs={'class': hidden_css}) for f in fields}


class DescriptionelternForm(forms.ModelForm):
    class Meta:
        model = Descriptioneltern
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Beschreiben Sie Ihre Familie und den Betreuungsbedarf (ohne sensible Details über Kinder)...'}),
        }


class BetreuungsZeitElternForm(forms.ModelForm):
    class Meta:
        model = BetreuungsZeitEltern
        fields = ['Mo_Vor', 'Di_Vor', 'Mi_Vor', 'Do_Vor', 'Fr_Vor', 'Sa_Vor', 'So_Vor',
                  'Mo_Nach', 'Di_Nach', 'Mi_Nach', 'Do_Nach', 'Fr_Nach', 'Sa_Nach', 'So_Nach',
                  'Mo_Ab', 'Di_Ab', 'Mi_Ab', 'Do_Ab', 'Fr_Ab', 'Sa_Ab', 'So_Ab',
                  'Mo_uberna', 'Di_uberna', 'Mi_uberna', 'Do_uberna', 'Fr_uberna', 'Sa_uberna', 'So_uberna']
        widgets = {f: forms.CheckboxInput(attrs={'class': 'form-check-input'}) for f in fields}


class NachrichtenForm(forms.ModelForm):
    class Meta:
        model = Nachrichten
        fields = ['meldung']
        widgets = {
            'meldung': forms.Textarea(attrs={'class': 'form-control', 'placeholder': ''}),
        }


class ProfilbildForm(forms.ModelForm):
    class Meta:
        model = Profilbild
        fields = ['bild']
        widgets = {
            'bild': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

    def clean_bild(self):
        bild = self.cleaned_data.get('bild')
        if not bild:
            return bild
        # For already-saved/default cases
        if not hasattr(bild, 'read'):
            return bild
        try:
            filename, content = process_profile_image(bild)
            content.name = filename
            return content
        except Exception as exc:
            raise forms.ValidationError(getattr(exc, 'message', str(exc)))


class ContactForm(forms.Form):
    email = forms.EmailField(label='E-Mail', max_length=254)
    message = forms.CharField(label='Nachricht', widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Nachricht'}))

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()
