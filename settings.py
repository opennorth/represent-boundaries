"""
To run `PYTHONPATH=$PYTHONPATH:$PWD django-admin.py migrate --settings settings --noinput`.
"""
import os

SECRET_KEY = 'x'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'represent_boundaries',
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.messages',
    'boundaries',
)

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if 'GDAL_LIBRARY_PATH' in os.environ:
    GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH')
if 'GEOS_LIBRARY_PATH' in os.environ:
    GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH')
