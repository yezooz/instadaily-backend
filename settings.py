# -*- coding: utf-8 -*-
import os.path

import sys

PROJECT_NAME = 'Instadaily'
SITE_DIR = 'instadaily/backend'
IS_FB = False
IS_TW = False

MAINTANCE_MODE = False

PROJECT_DIR = '/home/marek/' + SITE_DIR
LOCAL = False
DEBUG = False

TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG
INTERNAL_IPS = ['127.0.0.1', '168.168.1.2', '94.78.183.198', '69.63.187.251']

if LOCAL:
    db_user = 'root'
    db_pass = ''
else:
    db_user = 'root'
    db_pass = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'instadaily',  # Or path to database file if using sqlite3.
        'USER': db_user,  # Not used with sqlite3.
        'PASSWORD': db_pass,  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
    }
}

DATABASE_OPTIONS = {
    'charset': 'utf8',
}

if LOCAL:
    SITE_ROOT_URL = 'http://127.0.0.1:8000/'
    MEDIA_URL = 'http://127.0.0.1:8000/media/'
    STATIC_URL = 'http://127.0.0.1:8000/static/'
    SITE_URL = SITE_ROOT_URL
else:
    SITE_ROOT_URL = 'http://www.instadailyapp.com/'
    MEDIA_URL = 'http://www.instadailyapp.com/media/'
    STATIC_URL = 'http://www.instadailyapp.com/static/'
    SITE_URL = SITE_ROOT_URL

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'static') + '/'

SECRET_KEY = ''

ADMINS = (
    ('marek', 'marek.mikuliszyn@gmail.com'),
)
MANAGERS = ADMINS
ADMIN_UIDS = ('1',)  # , '2')

TIME_ZONE = 'Europe/London'

USE_I18N = False
USE_L10N = True
LANGUAGES = (
    ('en', 'English'),
    # ('pl', 'Polish'),
    # ('de', 'German')
)
LANGUAGE_CODE = 'en-us'

ROOT_URLCONF = 'urls'
APPEND_SLASH = True
SEND_BROKEN_LINK_EMAILS = False
SITE_ID = 1

# AUTH_PROFILE_MODULE = 'userprofile.userprofile'
# LOGIN_URL = '/accounts/login/'
# LOGOUT_URL = '/accounts/logout/'
# LOGIN_REDIRECT_URL = '/'

ACCOUNT_ACTIVATION_DAYS = 7

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'marek.mikuliszyn@gmail.com'
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587

DATE_FORMAT = 'Y-m-d'

SESSION_COOKIE_NAME = SITE_DIR + '_cookie'
# SESSION_COOKIE_AGE = 3600 * 24 # 24h
SESSION_COOKIE_AT_BROWSER_CLOSE = False

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

MIDDLEWARE_CLASSES = (
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'common.middleware.ProfilerMiddleware',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates')
)

INSTALLED_APPS = (
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.humanize',
    # 'django.contrib.flatpages',
    'django.contrib.messages',
    'annoying',
    'admin',
    'api',
    'auth',
    'www'
)

# AUTHENTICATION_BACKENDS = (
# 	'facebookconnect.models.FacebookBackend',
# 	'django.contrib.auth.backends.ModelBackend',
# )

TEMPLATE_CONTEXT_PROCESSORS = (
    # 'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    # 'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    # 'django.contrib.messages.context_processors.messages',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
