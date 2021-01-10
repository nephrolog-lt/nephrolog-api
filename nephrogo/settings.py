from pathlib import Path
import environ
import sentry_sdk
from django.utils.log import DEFAULT_LOGGING
import logging.config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')
if DEBUG:
    CELERY_TASK_ALWAYS_EAGER = True  # Sync celery tasks in sync

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY') if not DEBUG else 'DEBUG'
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS') if not DEBUG else []

USE_X_FORWARDED_HOST = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'drf_firebase_token_auth',

    'core.apps.CoreConfig',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    INSTALLED_APPS.append('django_admin_generator')

ROOT_URLCONF = 'nephrogo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'nephrogo.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
IS_POSTGRES_AVAILABLE = 'POSTGRES_DB' in env

if not DEBUG or IS_POSTGRES_AVAILABLE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env.str('POSTGRES_DB'),
            'USER': env.str('POSTGRES_USER'),
            'PASSWORD': env.str('POSTGRES_PASSWORD'),
            'HOST': env.str('POSTGRES_HOST'),
            'PORT': env.int('POSTGRES_POST'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'core.User'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = False

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_ROOT = BASE_DIR / 'static/'
STATIC_URL = '/static/'
MEDIA_ROOT = BASE_DIR / 'media/'
MEDIA_URL = '/media/'

SITE_ID = 1

# https://lincolnloop.com/blog/django-logging-right-way/
# Disable Django's logging setup
LOGGING_CONFIG = None
LOGGER_HANDLERS = ['console']
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)-12s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',  # STDERR
            'formatter': 'verbose',
        },
        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
    },
    'loggers': {
        '': {
            'level': 'WARNING',
            'handlers': LOGGER_HANDLERS,
        },
        'api': {
            'level': 'INFO' if DEBUG else 'WARNING',
            'handlers': LOGGER_HANDLERS,
            'propagate': False,
        },
        'core': {
            'level': 'INFO' if DEBUG else 'WARNING',
            'handlers': LOGGER_HANDLERS,
            'propagate': False,
        },
        # Default runserver request logging
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
    },
})

if not DEBUG:
    sentry_sdk.init(
        dsn=env.str('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )

# Rest framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.FirebaseAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),

    'COERCE_DECIMAL_TO_STRING': False,
}

DRF_FIREBASE_TOKEN_AUTH = {
    'FIREBASE_SERVICE_ACCOUNT_KEY_FILE_PATH': 'secrets/firebase.json',
    'AUTH_HEADER_TOKEN_KEYWORD': 'Bearer',
    'VERIFY_FIREBASE_TOKEN_NOT_REVOKED': False,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'NephroGo API',
    'DESCRIPTION': '',
    'TOS': None,
    'VERSION': '1.0.0',
    'SCHEMA_PATH_PREFIX': '/v1/',
    'SERVE_INCLUDE_SCHEMA': False,
    # Create separate components for PATCH endpoints (without required list)
    'COMPONENT_SPLIT_PATCH': False,
    # Split components into request and response parts where appropriate
    'COMPONENT_SPLIT_REQUEST': True,
    # Adds "blank" and "null" enum choices where appropriate. disable on client generation issues
    'ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE': False,
}