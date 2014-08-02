import os
import sys

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                'NAME': 'travis_ci_test',
                'USER': 'postgres' if os.getenv('CI', False) else '',
            }
        },
        ROOT_URLCONF='boundaries.urls',
        INSTALLED_APPS=(
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.gis',
            'boundaries',
        )
    )

if __name__ == '__main__':
    from django.test.simple import DjangoTestSuiteRunner
    runner = DjangoTestSuiteRunner(failfast=False)
    failures = runner.run_tests(['boundaries'])
    sys.exit(failures)
