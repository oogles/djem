# Minimal settings file to allow the generation of documentation on readthedocs.org.

SECRET_KEY = 'abcde12345'  # noqa: S105

# Need to point at something
ROOT_URLCONF = 'djem.tests'

MIDDLEWARE_CLASSES = []

# Install minimal apps - only to avoid import errors for autodoc
INSTALLED_APPS = [
    'django.contrib.contenttypes',  # for django.contrib.auth
    'django.contrib.auth'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
