from django.db import models
from django.contrib.auth.models import User


class Profileltern(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    plz = models.IntegerField(null=True, blank=True)
    ort = models.CharField(max_length=200, blank=True, default='')
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    is_public = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['lat', 'lon']),
            models.Index(fields=['is_public']),
        ]

    def approximate_ort(self):
        if self.plz:
            plz = str(self.plz)
            return f"Region {plz[:2]}xx" if len(plz) >= 2 else "Region unbekannt"
        return self.ort or ''


class Jobangebot(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    nanny = models.BooleanField("Nanny", default=False)
    tagesmutter = models.BooleanField("Tagesmutter", default=False)


class Anzahlkinder(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    ein_kind = models.BooleanField("1 Kind", default=False)
    zwei_kinder = models.BooleanField("2 Kinder", default=False)
    drei_kinder = models.BooleanField("3 Kinder", default=False)
    vier_plus_kinder = models.BooleanField("4+ Kinder", default=False)
    neugeborenes_baby = models.BooleanField("Neugeborenes Baby", default=False)
    kleinkind = models.BooleanField("kleinkind", default=False)
    kindergartenalter = models.BooleanField("kindergartenalter", default=False)
    schulalter = models.BooleanField("schulalter", default=False)
    teenager = models.BooleanField("teenager", default=False)


class Anfoderungeltern(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    essenzubereitung = models.BooleanField("Essenzubereitung", default=False)
    unterstutzung_bei_hausaufgaben = models.BooleanField("Unterstützung bei Hausaufgaben", default=False)
    bring_und_abholung = models.BooleanField("Bring- und Abholservice", default=False)
    leichte_haushaltarbeiten = models.BooleanField("Haushaltarbeiten", default=False)
    kind_fodern_beim_Sprechen = models.BooleanField("Kind födern beim Sprechen", default=False)


class BetreuungsZeitEltern(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    Mo_Vor = models.BooleanField("Mo_Vor", default=False)
    Di_Vor = models.BooleanField("Di_Vor", default=False)
    Mi_Vor = models.BooleanField("Mi_Vor", default=False)
    Do_Vor = models.BooleanField("Do_Vor", default=False)
    Fr_Vor = models.BooleanField("Fr_Vor", default=False)
    Sa_Vor = models.BooleanField("Sa_Vor", default=False)
    So_Vor = models.BooleanField("So_Vor", default=False)

    Mo_Nach = models.BooleanField("Mo_Nach", default=False)
    Di_Nach = models.BooleanField("Di_Nach", default=False)
    Mi_Nach = models.BooleanField("Mi_Nach", default=False)
    Do_Nach = models.BooleanField("Do_Nach", default=False)
    Fr_Nach = models.BooleanField("Fr_Nach", default=False)
    Sa_Nach = models.BooleanField("Sa_Nach", default=False)
    So_Nach = models.BooleanField("So_Nach", default=False)

    Mo_Ab = models.BooleanField("Mo_Ab", default=False)
    Di_Ab = models.BooleanField("Di_Ab", default=False)
    Mi_Ab = models.BooleanField("Mi_Ab", default=False)
    Do_Ab = models.BooleanField("Do_Ab", default=False)
    Fr_Ab = models.BooleanField("Fr_Ab", default=False)
    Sa_Ab = models.BooleanField("Sa_Ab", default=False)
    So_Ab = models.BooleanField("So_Ab", default=False)

    Mo_uberna = models.BooleanField("Mo_uberna", default=False)
    Di_uberna = models.BooleanField("Di_uberna", default=False)
    Mi_uberna = models.BooleanField("Mi_uberna", default=False)
    Do_uberna = models.BooleanField("Do_uberna", default=False)
    Fr_uberna = models.BooleanField("Fr_uberna", default=False)
    Sa_uberna = models.BooleanField("Sa_uberna", default=False)
    So_uberna = models.BooleanField("So_uberna", default=False)


class Descriptioneltern(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(
        "description", default="Ich bin auf der Suche nach einer fürsorglichen Nanny/Tagesmutter.")
