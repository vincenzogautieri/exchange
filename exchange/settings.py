"""
Django settings for exchange project.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
# Loaded from the environment — never hardcode it here.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY not found. Create a .env file (see .env.example) "
        "with a secret key before running this project."
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'app',
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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'exchange.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'exchange.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# Uses MongoDB via djongo. Connection details are read from the environment
# so no real host/credentials ever need to be hardcoded here.

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': os.environ.get('MONGO_DB_NAME', 'exchange_data'),
        'CLIENT': {
            'host': os.environ.get('MONGO_HOST', 'localhost'),
            'port': int(os.environ.get('MONGO_PORT', 27017)),
            'username': os.environ.get('MONGO_USERNAME', ''),
            'password': os.environ.get('MONGO_PASSWORD', ''),
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
