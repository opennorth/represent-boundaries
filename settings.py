"""
To run `PYTHONPATH=$PYTHONPATH:$PWD django-admin.py migrate --settings settings --noinput`.
"""

SECRET_KEY = 'x'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'travis_ci_test',
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'boundaries',
)
