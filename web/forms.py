from django.contrib.auth.forms import UserCreationForm
from django import forms

from django.contrib.auth.models import User
from .models import Anfoderungeltern, Angabejob, BetreuungsZeitEltern, Nachrichten, Profil, Description, Experiencechild, AdditionalSkillsChild, Profilbild, Profileltern, Anzahlkinder, Anfoderungeltern, Descriptioneltern, Jobangebot

hidden_css = 'hidden css-eingeben'
# NannyINSERAT
class ProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        YEARS = [x for x in range(1955, 2021)]
        fields = ['plz', 'ort', 'salary', 'birth_date']
        widgets = {
            'plz': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'PLZ'}),
            'ort': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ort'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control profiltierbetreuer', 'placeholder': 'Gewünschter Stundenlohn'}),
            'birth_date': forms.SelectDateWidget(years=YEARS, attrs={'class': 'form-select datum', })
        }


class AngabejobForm(forms.ModelForm):
    class Meta:
        model = Angabejob
        fields = ['angabe_job_nanny', 'angabe_job_tagesmutter']
        widgets = {
            'angabe_job_nanny': forms.CheckboxInput(attrs={'class': hidden_css}),
            'angabe_job_tagesmutter': forms.CheckboxInput(attrs={'class': hidden_css}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nachname'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Passwort'}),
        }

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username','password1','password2']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nachname'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E-Mail'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Passwort'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Passwort wiederholen'}),
        }

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        username = self.cleaned_data["username"]
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
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'z.B. Freut mich das Ihr nach meinem Profil vorbeischaut. Erfahrung habe ich im Bereich der Betreuung von Säuglingen bis zur Schulkinder gesammelt. Ich bin ein Verantwortungsbewusste, Herzliche und geduldige Person. Zu dem gehört das ich sehr gerne mit den Kinder unternehme Zuhause sowie auch Draussen an den Spielplatz, Ausflüge und sonstige Kinder Aktivitäten. Gerne übernehme ich auf Wunsch leichte Haushaltaufgaben wie das Essen zubereiten. Bei Anfragen sende ich gerne meinen Lebenslauf und Arbeitszeugnis zu. '})
        }


class ExperiencechildForm(forms.ModelForm):
    class Meta:
        model = Experiencechild
        fields = ['newborn_child_experience', 'infants_child_experience',
                  'kindergarden_school_child_experience']
        widgets = {
            'newborn_child_experience': forms.CheckboxInput(attrs={'class': hidden_css}),
            'infants_child_experience': forms.CheckboxInput(attrs={'class': hidden_css}),
            'kindergarden_school_child_experience': forms.CheckboxInput(attrs={'class': hidden_css})
        }


class AdditionalSkillsChildForm(forms.ModelForm):
    class Meta:
        model = AdditionalSkillsChild
        fields = ['fachfrau_course','sitting_course', 'drivers_licence','study','ausbildung','praktikum','arbeitserfahrung']
        widgets = {
            'fachfrau_course': forms.CheckboxInput(attrs={'class': hidden_css}),
            'sitting_course': forms.CheckboxInput(attrs={'class': hidden_css}),
            'drivers_licence': forms.CheckboxInput(attrs={'class': hidden_css}),
            'study': forms.CheckboxInput(attrs={'class': hidden_css}),
            'ausbildung': forms.CheckboxInput(attrs={'class': hidden_css}),
            'praktikum': forms.CheckboxInput(attrs={'class': hidden_css}),
            'arbeitserfahrung': forms.CheckboxInput(attrs={'class': hidden_css})

        }


# ElternINSERAT
class ProfilelternForm(forms.ModelForm):
    class Meta:
        model = Profileltern
        fields = ['plz', 'ort']
        widgets = {
            'plz': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'PLZ'}),
            'ort': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ort'}),
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
        widgets = {
            'ein_kind': forms.CheckboxInput(attrs={'class': hidden_css}),
            'zwei_kinder': forms.CheckboxInput(attrs={'class': hidden_css}),
            'drei_kinder': forms.CheckboxInput(attrs={'class': hidden_css}),
            'vier_plus_kinder': forms.CheckboxInput(attrs={'class': hidden_css}),
            'neugeborenes_baby': forms.CheckboxInput(attrs={'class': hidden_css}),
            'kleinkind': forms.CheckboxInput(attrs={'class': hidden_css}),
            'kindergartenalter': forms.CheckboxInput(attrs={'class': hidden_css}),
            'schulalter': forms.CheckboxInput(attrs={'class': hidden_css}),
            'teenager': forms.CheckboxInput(attrs={'class': hidden_css}),

        }


class AnfoderungelternForm(forms.ModelForm):
    class Meta:
        model = Anfoderungeltern
        fields = ['essenzubereitung', 'unterstutzung_bei_hausaufgaben',
                  'bring_und_abholung', 'leichte_haushaltarbeiten', 'kind_fodern_beim_Sprechen']
        widgets = {
            'essenzubereitung': forms.CheckboxInput(attrs={'class': hidden_css}),
            'unterstutzung_bei_hausaufgaben': forms.CheckboxInput(attrs={'class': hidden_css}),
            'bring_und_abholung': forms.CheckboxInput(attrs={'class': hidden_css}),
            'leichte_haushaltarbeiten': forms.CheckboxInput(attrs={'class': hidden_css}),
            'kind_fodern_beim_Sprechen': forms.CheckboxInput(attrs={'class': hidden_css}),
        }


class DescriptionelternForm(forms.ModelForm):
    class Meta:
        model = Descriptioneltern
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'z.B. Wir sind eine junge Familie mit 3 Kindern und suchen ab den 08/20XX eine liebevolle, tatkräftige Nanny für unsere drei Kinder, 4, 9  und 11 Jahre alt. Arbeitspensum währe 50% jeweils Dienstag & Donnerstag. Aufgaben währen z.B: Mittagessen kochen, Spielzeug Aufräumen und leichte Hausarbeit. Die Kinder müssten bei den Hausaufgaben unterstützt werden sowie bei der Freizeitaktivitäten begleitet werden. Die Kinder sind sehr kontaktfreudig und es macht viel Freude, Zeit mit ihnen zu verbringen. Uns ist es wichtig, das Sie gerne Zeit mit den Kindern verbringen. Ziel ist ein langfristiges Arbeitsverhältnis mit Festanstellung und mit geregelten Rahmenbedingungen bei korrekter Bezahlung. Wir freuen uns auf Ihre Bewerbung. Voraussetzungen: Referenzen, Erfahrung im Umgang mit Kindern, Sprachkenntnisse Deutsch oder Englisch.'}),
        }

class BetreuungsZeitElternForm(forms.ModelForm):
    class Meta:
        model = BetreuungsZeitEltern
        fields = ['Mo_Vor', 'Di_Vor', 'Mi_Vor',
                  'Do_Vor', 'Fr_Vor', 'Sa_Vor', 'So_Vor', 'Mo_Nach', 'Di_Nach', 'Mi_Nach',
                  'Do_Nach', 'Fr_Nach', 'Sa_Nach', 'So_Nach', 'Mo_Ab', 'Di_Ab', 'Mi_Ab',
                  'Do_Ab', 'Fr_Ab', 'Sa_Ab', 'So_Ab', 'Mo_uberna', 'Di_uberna', 'Mi_uberna',
                  'Do_uberna', 'Fr_uberna', 'Sa_uberna', 'So_uberna']
        widgets = {
            'Mo_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Di_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Mi_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Do_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Fr_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Sa_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'So_Vor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'Mo_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Di_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Mi_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Do_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Fr_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Sa_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'So_Nach': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'Mo_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Di_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Mi_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Do_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Fr_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Sa_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'So_Ab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'Mo_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Di_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Mi_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Do_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Fr_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'Sa_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'So_uberna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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
            'bild': forms.FileInput(attrs={'class': 'form-control'})
        }