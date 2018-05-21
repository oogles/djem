# Minimal settings file to allow the running of tests, execution of migrations,
# and several other useful management commands.

SECRET_KEY = 'abcde12345'

# Needs to point to something to allow tests to perform url resolving. The file
# doesn't actually need to contain any urls (but does need to define "urlpatterns").
ROOT_URLCONF = 'djem.tests'

# For TimeZoneHelper/TimeZoneField tests
USE_TZ = True

INSTALLED_APPS = [
    'django.contrib.contenttypes',  # for django.contrib.auth
    'django.contrib.auth',          # for tests
    'django.contrib.messages',      # for tests
    
    'djem',
    'djem.tests',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

# For testing template tags
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.contrib.auth.context_processors.auth'
        ],
    },
}]

# Add django-extensions to INSTALLED_APPS if it is present. This provides extra
# dev tools, e.g. shell_plus, but isn't required - e.g. for testing.
try:
    import django_extensions  # noqa: F401 (import unused)
except ImportError:
    pass
else:
    INSTALLED_APPS.append('django_extensions')
    
    SHELL_PLUS_POST_IMPORTS = (
        ('djem.utils.dev', 'Developer'),
        ('djem.utils.mon', 'Mon'),
        ('djem.utils.inspect', 'pp'),
    )
