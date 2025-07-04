from django.contrib import admin

from web.models.models_subscription import Price, Subscription

# Register your models here.
from .models import Angabejob, Anzahlkinder,  BetreuungsZeitEltern, Descriptioneltern, Jobangebot, Profil, Description, Experiencechild, AdditionalSkillsChild, Profilbild, Profileltern, Nachrichten, Anfoderungeltern

admin.site.register(Profil)
admin.site.register(Description)
admin.site.register(Experiencechild)
admin.site.register(AdditionalSkillsChild)
admin.site.register(Angabejob)

admin.site.register(Nachrichten)
admin.site.register(Profileltern)
admin.site.register(Jobangebot)
admin.site.register(Anfoderungeltern)
admin.site.register(Anzahlkinder)
admin.site.register(Descriptioneltern)
admin.site.register(BetreuungsZeitEltern)
admin.site.register(Profilbild)

admin.site.register(Subscription)
admin.site.register(Price)