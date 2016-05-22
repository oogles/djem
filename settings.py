# Minimal settings file to allow the running of tests, execution of migrations,
# and several other useful management commands.

SECRET_KEY = 'abcde12345'

# For testing. If django-goodies ever includes real views that also need testing,
# this should point to that urlconf and the test app's urls should be tested
# by overriding the setting.
ROOT_URLCONF = 'django_goodies.tests.app.urls'

# For TimeZoneHelper/TimeZoneField tests
USE_TZ = True

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',  # for AjaxResponse tests
    'django.contrib.messages.middleware.MessageMiddleware'   # for AjaxResponse tests
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',  # for django.contrib.auth
    'django.contrib.auth',          # for various tests
    'django.contrib.messages',      # for AjaxResponse tests
    
    'django_extensions',  # for dev tools, e.g. shell_plus
    
    'django_goodies',
    'django_goodies.tests.app',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

# For object-level permissions framework tests
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_goodies.auth.ObjectPermissionsBackend'
]
