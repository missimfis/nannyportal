from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


class Profil(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    plz = models.IntegerField(default=None, null=True, blank=True)
    ort = models.CharField(max_length=200, blank=True, default='')
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    birth_date = models.DateTimeField('Geburtstag', null=True, blank=True)
    salary = models.DecimalField("Stundenlohn", max_digits=5, decimal_places=2, null=True, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['lat', 'lon']),
            models.Index(fields=['is_public']),
        ]

    def calculate_age(self):
        if not self.birth_date:
            return None
        today = timezone.now()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def age_range(self):
        age = self.calculate_age()
        if age is None:
            return ''
        if age < 18:
            return 'unter 18'
        lower = (age // 5) * 5
        upper = lower + 4
        return f"{lower}-{upper}"

    def approximate_ort(self):
        if self.plz:
            plz = str(self.plz)
            # show coarse area (first digits / region hint) instead of full exact place details where possible
            return f"Region {plz[:2]}xx" if len(plz) >= 2 else "Region unbekannt"
        return self.ort or ''


class Angabejob(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    angabe_job_nanny = models.BooleanField("Als Nanny", default=False)
    angabe_job_tagesmutter = models.BooleanField("Als Tagesmutter", default=False)


class Description(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(
        "description", default="Ich bin auf der Suche nach einem Job als Nanny oder Tagesmutter.")


class Experiencechild(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    newborn_child_experience = models.BooleanField("Neugeborenen", default=False)
    infants_child_experience = models.BooleanField("Kleinkind", default=False)
    kindergarden_school_child_experience = models.BooleanField(
        "Kindergarten- und Schulalter", default=False)


class AdditionalSkillsChild(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    fachfrau_course = models.BooleanField("Fachmann/-frau Betreuung EFZ", default=False)
    sitting_course = models.BooleanField("Babysitting-Kurs", default=False)
    drivers_licence = models.BooleanField("Führerschein ", default=False)
    study = models.BooleanField("Studium", default=False)
    ausbildung = models.BooleanField("Ausbildung EFZ", default=False)
    praktikum = models.BooleanField("Praktikum", default=False)
    arbeitserfahrung = models.BooleanField("Arbeitserfahrung", default=False)
