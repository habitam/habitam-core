# -*- coding: utf-8 -*-
# Django settings for habitam project.
from decimal import Decimal
from django.conf import global_settings
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG
BASE_DIR = '/Users/stefan/repositories/habitam'

ADMINS = (
    ('Stefan Guna', 'svguna@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_DIR, 'sqlite.db'),  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Bucharest'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ro'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'fu8*jxa4ml52n0^)2xw^5rx0kt$=@4!0io2&cwus8hayxuc-2t'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'habitam.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'habitam.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'habitam.entities',
    'habitam.financial',
    'habitam.ui',
    'habitam.licensing',
    'habitam.payu',
    'registration',
    'captcha',
    'social_auth',
    'habitam.social'
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    'social_auth.backends.facebook.FacebookBackend',
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.yahoo.YahooBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.associate.associate_by_email',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'habitam.social.auth.notify',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details'
)

GOOGLE_OAUTH2_CLIENT_ID = None
GOOGLE_OAUTH2_CLIENT_SECRET = None
FACEBOOK_APP_ID = None
FACEBOOK_API_SECRET = None
FACEBOOK_EXTENDED_PERMISSIONS = ['email']

TWITTER_CONSUMER_KEY = None
TWITTER_CONSUMER_SECRET = None

YAHOO_CONSUMER_KEY = None
YAHOO_CONSUMER_SECRET = None

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/ui'
SOCIAL_AUTH_COMPLETE_URL_NAME = 'socialauth_complete'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'socialauth_associate_complete'
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
ACCOUNT_ACTIVATION_DAYS = 2

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'habitam': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    "habitam.ui.context_processors.google_analytics",
)

GA_ACCOUNT_ID = ''
GA_URL = ''

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = '"Habitam.ro" <office@habitam.ro>'
SENDER = 'office@habitam.ro'

CONTACT_EMAIL = 'office@habitam.ro'

# APPLICATION CONFIGURATION

PAYU_DEBUG = True
PAYU_TIMEOUT = 5
PAYU_TRANSACTION_CHARGE = Decimal(0.025)

# The maximum day of the month after which no more payments are received
MAX_CLOSE_DAY = 28
# The maximum number of days after payment list issuance when debts should be
# paid
MAX_PAYMENT_DUE_DAYS = 20
# The number of days after the payment deadline when penalties start to be
# calculated
PENALTY_START_DAYS = 30
# The maximum penalty percentage per day
MAX_PENALTY_PER_DAY = .2

EPS = Decimal('0.01')

TRIAL_LICENSE = {
    'max_apartments' : 100,
    'months_back': 2,
    'days_valid': 60
}

COUNTIES_TUPLE = (('Alba', 'Alba'), ('Arad', 'Arad'), ('Arges', u'Argeș'),
    ('Bacau', u'Bacău'), ('Bihor', 'Bihor'),
    ('Bistrita-Nasaud', u'Bistrița-Năsăud'),
    ('Botosani', u'Botoșani'), ('Braila', u'Brăila'), ('Brasov', u'Brașov'),
    ('Bucuresti', u'București'), ('Buzau', u'Buzău'),
    ('Calarasi', u'Călărași'), ('Caras-Severin', u'Caraș-Severin'),
    ('Cluj', 'Cluj'), ('Constanta', u'Constanța'), ('Covasna', 'Covasna'),
    ('Dambovita', u'Dâmbovița'), ('Dolj', u'Dolj'), ('Galati', u'Galați'),
    ('Giurgiu', 'Giurgiu'), ('Gorj', 'Gorj'), ('Harghita', 'Harghita'),
    ('Hunedoara', 'Hunedoara'), ('Ialomita', u'Ialomița'), ('Iasi', u'Iasi'),
    ('Ilfov', 'Ilfov'), ('Maramures', u'Maramureș'),
    ('Mehedinti', u'Mehedinți'), ('Mures', u'Mureș'), ('Neamt', u'Neamț'),
    ('Olt', 'Olt'), ('Prahova', 'Prahova'), ('Salaj', u'Sălaj'),
    ('Satu-Mare', 'Satu-Mare'), ('Sibiu', 'Sibiu'), ('Suceava', 'Suceava'),
    ('Teleorman', 'Teleorman'), ('Timis', u'Timiș'), ('Tulcea', 'Tulcea'),
    ('Valcea', u'Vâlcea'), ('Vaslui', 'Vaslui'), ('Vrancea', 'Vrancea'))
DEFAULT_COUNTY = 'Bucuresti'
