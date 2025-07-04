from django.db import models
from django.contrib.auth.models import User

# ELTERNINSERAT
class Profileltern(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    plz = models.IntegerField()
    ort = models.CharField(max_length=200)
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)


class Jobangebot(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    nanny = models.BooleanField("Nanny")
    tagesmutter = models.BooleanField("Tagesmutter")


class Anzahlkinder(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    ein_kind = models.BooleanField("1 Kind")
    zwei_kinder = models.BooleanField("2 Kinder")
    drei_kinder = models.BooleanField("3 Kinder")
    vier_plus_kinder = models.BooleanField("4+ Kinder")
    neugeborenes_baby = models.BooleanField("Neugeborenes Baby")
    kleinkind = models.BooleanField("kleinkind")
    kindergartenalter = models.BooleanField("kindergartenalter")
    schulalter = models.BooleanField("schulalter")
    teenager = models.BooleanField("teenager")


class Anfoderungeltern(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    essenzubereitung = models.BooleanField("Essenzubereitung")
    unterstutzung_bei_hausaufgaben = models.BooleanField(
        "Unterstützung bei Hausaufgaben")
    bring_und_abholung = models.BooleanField("Bring- und Abholservice")
    leichte_haushaltarbeiten = models.BooleanField("Haushaltarbeiten")
    kind_fodern_beim_Sprechen = models.BooleanField(
        "Kind födern beim Sprechen", default=False)


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
