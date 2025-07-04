from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
# NANNYNSERAT

class Profil(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    plz = models.IntegerField(default=None)
    ort = models.CharField(max_length=200)
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    birth_date = models.DateTimeField('Geburtstag')
    salary = models.DecimalField("Stundenlohn", max_digits=5, decimal_places=2)

    def calculate_age(self):
        today = timezone.now()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

class Angabejob(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    angabe_job_nanny = models.BooleanField("Als Nanny")
    angabe_job_tagesmutter = models.BooleanField("Als Tagesmutter")


class Description(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(
        "description", default="Ich bin auf der Suche nach einem Job als Nanny oder Tagesmutter.")


class Experiencechild(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    newborn_child_experience = models.BooleanField("Neugeborenen")
    infants_child_experience = models.BooleanField("Kleinkind")
    kindergarden_school_child_experience = models.BooleanField(
        "Kindergarten- und Schulalter")


class AdditionalSkillsChild(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    fachfrau_course = models.BooleanField(
        "Fachmann/-frau Betreuung EFZ", default=False)
    sitting_course = models.BooleanField("Babysitting-Kurs")
    drivers_licence = models.BooleanField("Führerschein ")
    study = models.BooleanField("Studium", default=False)
    ausbildung = models.BooleanField("Ausbildung EFZ", default=False)
    praktikum = models.BooleanField("Praktikum", default=False)
    arbeitserfahrung = models.BooleanField("Arbeitserfahrung", default=False)

