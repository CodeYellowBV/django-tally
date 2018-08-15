import os

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    } if (
        os.path.exists('/.dockerenv') and
        not os.environ.get('CY_INSIDE_TRAVIS')
    ) else {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'django-tally-test',
    },
}

INSTALLED_APPS = [
    'django_tally.data',
    'django_tally.user_def',
    'tests.testapp',
]

MIGRATION_MODULES = {
    'data': None,
    'user_def': None,
    'testapp': None,
}

ROOT_URLCONF = 'tests.testapp.urls'

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # We override only this one to avoid logspam while running tests.
        # Django warnings are still shown.
        'buckets': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    }
}
