# Minimal settings file to allow the generation of documentation on readthedocs.org.

SECRET_KEY = 'abcde12345'

# Need to point at something
ROOT_URLCONF = 'django_goodies.tests.app.urls'

MIDDLEWARE_CLASSES = ()

INSTALLED_APPS = ()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
