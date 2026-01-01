# Minimal settings file to allow the running of tests, execution of migrations,
# and several other useful management commands.

SECRET_KEY = 'abcde12345'  # nosec

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
    'djem_dev',  # for dev utils, such as extended auto-imports in `shell` command
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

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'  # suppress system check warning
