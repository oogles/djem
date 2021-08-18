import re
import warnings

from django.apps import AppConfig, apps
from django.template import engines
from django.test import RequestFactory

from djem.middleware import MemoryStorage

BETWEEN_TAG_WHITESPACE_RE = re.compile(r'>\s+<')
EXCESS_WHITESPACE_RE = re.compile(r'\s\s+')


def setup_test_app(package, label=None):
    """
    Setup a Django test app for the provided package to allow test-only models
    to be used.
    
    This function should be called from ``myapp.tests.__init__`` like so::
    
        setup_test_app(__package__)
    
    This will create an app with the label "myapp_tests". If a specific app
    label is required, it can be provided explicitly::
    
        setup_test_app(__package__, 'mytests')
    
    Using either of the above, models can be placed in ``myapp.tests.models``
    and be discovered and used just like regular models by the test suite. As
    long as ``myapp.tests`` is not imported by anything that forms part of the
    standard Django runtime environment, these models will not be picked up in
    that environment, and will be isolated to the test suite only.
    """
    
    #
    # This solution is adapted from Simon Charette's comment on Django ticket #7835:
    # https://code.djangoproject.com/ticket/7835#comment:46
    #
    
    if label is None:
        containing_app_config = apps.get_containing_app_config(package)
        label = containing_app_config.label
        
        # Only suffix the app label if it has not been already. This allows
        # duplicate entries to be detected and prevented. It may prevent the
        # use of an implicit label if the tests reside in an app that
        # legitimately ends with "_tests", but an explicit label can always be
        # used. Without this check, earlier entries are returned by
        # get_containing_app_config() and suffixed repeatedly.
        if not containing_app_config.label.endswith('_tests'):
            label = '{}_tests'.format(containing_app_config.label)
    
    if label in apps.app_configs:
        # An app with this label already exists, skip adding it. This is
        # necessary (vs raising an exception) as there are certain conditions
        # that can cause this function to be run multiple times (e.g. errors
        # during Django's initialisation can cause this).
        warnings.warn(f'Attempted setup of duplicate test app "{label}".', RuntimeWarning)
    
    app_config = AppConfig.create(package)
    app_config.apps = apps
    app_config.label = label
    
    apps.app_configs[label] = app_config
    
    app_config.import_models()
    
    apps.clear_cache()


class MessagingRequestFactory(RequestFactory):
    """
    An extension of Django's ``RequestFactory`` helper for tests that enables
    the use of the messages framework within the generated request. It does not
    use the standard message storage backend (as per the ``MESSAGE_STORAGE``
    setting), but rather a memory-only backend that does not involve the use
    of sessions, cookies or any other means of persistent storage of the
    messages. Thus, messages need to be read in the same request they were
    added, or they will be lost.
    """
    
    def request(self, **request):
        
        request = super().request(**request)
        
        # Patch the request so it appears as though the
        # djem.middleware.MessageMiddleware is in use, and it is an AJAX request
        request._messages = MemoryStorage(request)
        
        return request


class TemplateRendererMixin:
    """
    A mixin for TestCase classes whose tests render templates from strings (as
    opposed to rendering them from files), using the Django template engine.
    """
    
    def render_template(self, template_string, context, request=None, flatten=True):
        """
        Render the given string as a template, with the given context and
        request (if provided).
        
        If ``request`` is NOT provided, and a ``self.user`` attribute is
        available on the ``TestCase``, a "user" variable will be automatically
        added to the context.
        
        The rendered output will be stripped of any leading or trailing
        whitespace, and can optionally have excess whitespace "flattened" by
        passing the ``flatten`` argument as True (the default). Flattening
        removes ALL whitespace from between HTML tags and compresses all other
        whitespace down to a single space.
        
        :param template_string: The string to render as a template.
        :param context: The context with which to render the template.
        :param request: The ``HttpRequest`` with which to render the template context.
        :param flatten: True to "flatten" the rendered output (default), False
            to return the output with all internal whitespace intact.
        :return: The rendered template output.
        """
        
        if not request:
            try:
                context['user'] = self.user
            except AttributeError:
                pass
        
        output = engines['django'].from_string(template_string).render(context, request)
        
        if flatten:
            # Remove whitespace between tags
            output = re.sub(BETWEEN_TAG_WHITESPACE_RE, '><', output)
            
            # Replace instances of multiple whitespace characters with a single space
            output = re.sub(EXCESS_WHITESPACE_RE, ' ', output)
        
        return output.strip()  # remove unnecessary whitespace
