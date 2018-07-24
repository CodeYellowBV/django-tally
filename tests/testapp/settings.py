DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = [
    'django_tally.data',
    'django_tally.user_def',
    'tests.testapp',
]

MIGRATION_MODULES = {
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
