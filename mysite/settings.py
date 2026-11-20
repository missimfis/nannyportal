"""
Django settings for mysite project.
"""

from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if env_bool("DJANGO_ALLOW_INSECURE_DEFAULTS", False) or os.getenv("PYTHONDONTWRITEBYTECODE") == "1":
        # Development/CI convenience only. Production must set SECRET_KEY.
        SECRET_KEY = "django-insecure-change-me"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DEBUG", False)

# Hosts / proxy / CSRF
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

# Only enable when the reverse proxy strips/sets X-Forwarded-Proto consistently.
if env_bool("SECURE_PROXY_SSL_HEADER_ENABLED", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", False)

# HTTPS / cookies
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", str(60 * 60 * 8)))  # 8h default
SESSION_EXPIRE_AT_BROWSER_CLOSE = env_bool("SESSION_EXPIRE_AT_BROWSER_CLOSE", False)
SESSION_SAVE_EVERY_REQUEST = env_bool("SESSION_SAVE_EVERY_REQUEST", True)
CSRF_COOKIE_AGE = int(os.getenv("CSRF_COOKIE_AGE", str(60 * 60 * 8)))
CSRF_USE_SESSIONS = env_bool("CSRF_USE_SESSIONS", False)
PASSWORD_RESET_TIMEOUT = int(os.getenv("PASSWORD_RESET_TIMEOUT", str(60 * 60)))

# HSTS: enable only after HTTPS is verified end-to-end. Roll out in stages.
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0" if DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = os.getenv("SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = "DENY"

FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("FILE_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024)))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("DATA_UPLOAD_MAX_MEMORY_SIZE", str(10 * 1024 * 1024)))
PROFILE_IMAGE_MAX_BYTES = int(os.getenv("PROFILE_IMAGE_MAX_BYTES", str(5 * 1024 * 1024)))

# Email
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# Application definition
INSTALLED_APPS = [
    'web.apps.WebConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'web.middleware.SimpleRateLimitMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'web' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

DECIMAL_SEPARATOR = '.'

# Database: SQLite for local dev by default; configure PostgreSQL via env in production.
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")
if DB_ENGINE.endswith("sqlite3"):
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.getenv("DB_NAME", str(BASE_DIR / 'db.sqlite3')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.getenv("DB_NAME", ""),
            'USER': os.getenv("DB_USER", ""),
            'PASSWORD': os.getenv("DB_PASSWORD", ""),
            'HOST': os.getenv("DB_HOST", ""),
            'PORT': os.getenv("DB_PORT", ""),
            'CONN_MAX_AGE': int(os.getenv("DB_CONN_MAX_AGE", "60")),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'de'
TIME_ZONE = 'Europe/Zurich'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('de', _('German')),
    ('en', _('English')),
]
LOCALE_PATHS = (os.path.join(BASE_DIR, 'web/locale/'),)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "web/media/")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = "web:redirection"
LOGOUT_REDIRECT_URL = "web:index"

CACHES = {
    'default': {
        'BACKEND': os.getenv('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': os.getenv('CACHE_LOCATION', 'nannyportal-ratelimit'),
    }
}

# Simple in-app rate limiting defaults (requests per window seconds)
RATE_LIMIT_LOGIN = os.getenv('RATE_LIMIT_LOGIN', '10/300')
RATE_LIMIT_PASSWORD_RESET = os.getenv('RATE_LIMIT_PASSWORD_RESET', '5/900')
RATE_LIMIT_SIGNUP = os.getenv('RATE_LIMIT_SIGNUP', '10/3600')
RATE_LIMIT_CONTACT = os.getenv('RATE_LIMIT_CONTACT', '10/3600')
RATE_LIMIT_MESSAGE = os.getenv('RATE_LIMIT_MESSAGE', '60/300')

# Geocoding: keep off request path by default
GEOCODE_ON_SAVE = env_bool('GEOCODE_ON_SAVE', False)
GEOCODING_USER_AGENT = os.getenv('GEOCODING_USER_AGENT', 'nannyportal')
GEOCODING_DOMAIN = os.getenv('GEOCODING_DOMAIN', 'photon.komoot.io')

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': os.getenv('LOG_LEVEL', 'INFO')},
}
