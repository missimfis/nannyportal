from django.conf.urls import include
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from web.views.views_general import AgbView, ContactView, DataProtectionView, HelpView, UeberUnsView, SettingsView

from web.views.views_subscription import (
    CancelView,
    CreateCheckoutSessionView,
    SuccessView,
    SubscriptionPageView,
    stripe_webhook,
)

from . import views

app_name = 'web'
urlpatterns = [
    path('', views.index, name='index'),
    path('logout_view', views.logout_view, name='logout_view'),
    path('register', views.register, name='register'),
    path('create-user/<int:group_id>', views.create_user, name='create-user'),
    path('delete-user', views.delete_user, name='delete-user'),
    path('kasse/<int:abo>', views.kasse, name='kasse'),
    path('redirection', views.redirection, name='redirection'),
    path('schnuppern', views.schnuppern, name='schnuppern'),
    path('subscription', SubscriptionPageView.as_view(), name="subscription"),
    path('create-checkout-session/<int:pk>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('cancel', CancelView.as_view(), name="cancel"),
    path('success', SuccessView.as_view(), name="success"),
    path('stripe/webhook', stripe_webhook, name="stripe-webhook"),

    # footer navigation

    path('contact', ContactView.as_view(), name='contact'),
    path('help', HelpView.as_view(), name='help'),
    path('agb', AgbView.as_view(), name='agb'),
    path('dataprotection', DataProtectionView.as_view(), name='dataprotection'),
    path('ueberuns', UeberUnsView.as_view(), name='ueberuns'),

    # nanny urls
    path('create-profil', views.create_profil, name='create-profil'),
    path('angabejob', views.createangabejob, name='angabejob'),
    path('create-description', views.create_description, name='create-description'),
    path('experiencechild', views.experiencechild, name='experiencechild'),
    path('additionalskillschild', views.additionalskillschild,name='additionalskillschild'),
    path('dateinanny', views.dateinanny, name='dateinanny'),


    path('profilnanny', views.profil_nanny, name='profilnanny'),
    path('profilnanny/<int:user_id>', views.profil_nanny, name='profilnanny'),
    path('startseitenanny', views.startseitenanny, name='startseitenanny'),
    path('bearbeitungnanny', views.bearbeitungnanny, name='bearbeitungnanny'),
    path('premiumnanny', views.premiumnanny, name='premiumnanny'),


    # eltern urls
    path('create-profil-eltern', views.create_profil_eltern,name='create-profil-eltern'),
    path('jobangebot', views.jobangebot, name='jobangebot'),
    path('anzahl-kinder', views.anzahlkinder, name='anzahl-kinder'),
    path('anfoderungeltern', views.anfoderungeltern, name='anfoderungeltern'),
    path('descriptioneltern', views.descriptioneltern, name='descriptioneltern'),
    path('betreuungszeiteltern', views.betreuungszeiteltern, name='betreuungszeiteltern'),
    path('datei', views.datei, name='datei'),


    path('profileltern', views.profileltern, name='profileltern'),
    path('profileltern/<int:user_id>', views.profileltern, name='profileltern'),
    path('nachrichten', views.nachrichten, name='nachrichten'),
    path('nachrichten/<int:empfaenger_id>', views.nachrichten, name='nachrichten'),
    path('startseiteeltern', views.startseiteeltern, name='startseiteeltern'),
    path('premiumeltern', views.premiumeltern, name='premiumeltern'),
    path('einstellungen', SettingsView.as_view(), name='einstellungen'),
    path('bearbeitungelternprofil',views.bearbeitungelternprofil,name='bearbeitungelternprofil')
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
