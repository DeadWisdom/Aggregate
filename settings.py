import os


### App Settings ###
AGGREGATE_STALE = 60 * 5      # 5 minutes
EXTRA_APPS = ( 'aggregate', )


### Project Settings ###
DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = ''
DATABASE_NAME = ''
DATABASE_USER = ''
DATABASE_PASSWORD = ''

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SECRET_KEY = 'sl3p+a4ir7l(6+-hujwjjmzbe!41zzom_-90*wpqas5aup$b8*'
SITE_ID = 1

MEDIA_ROOT = os.path.abspath( os.path.join(__file__, '..', 'media') )
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin/media/'

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
) + EXTRA_APPS


### Local Settings ###
try:
    from settings_local import *
except ImportError:
    pass
