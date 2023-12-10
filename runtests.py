import os
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                'NAME': 'postgres' if os.getenv('CI', False) else 'represent_boundaries_test',
                'USER': 'postgres' if os.getenv('CI', False) else '',
                'PASSWORD': 'postgres' if os.getenv('CI', False) else '',
                'PORT': os.getenv('PORT', 5432),
            }
        },
        ROOT_URLCONF='boundaries.urls',
        INSTALLED_APPS=(
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.gis',
            'django.contrib.sessions',
            'django.contrib.messages',
            'boundaries',
        ),
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[
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
        ],
    )
    django.setup()

if __name__ == '__main__':
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(failfast=False)
    failures = runner.run_tests(['boundaries'])
    sys.exit(failures)
