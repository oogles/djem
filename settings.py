# Minimal settings file to allow the running of tests, execution of migrations,
# and several other useful management commands.

SECRET_KEY = 'abcde12345'

# Need to point at something. If django-goodies actually uses urls one day,
# this file should live in the django_goodies app directory.
ROOT_URLCONF = 'urls'

MIDDLEWARE_CLASSES = ()

INSTALLED_APPS = (
    'django.contrib.contenttypes',  # for django.contrib.auth
    'django.contrib.auth',  # for RequestFactoryTestCase
    
    'django_extensions',  # for dev tools, e.g. shell_plus
    
    'django_goodies',
    'django_goodies.tests',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
