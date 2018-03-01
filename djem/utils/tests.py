import re

from django.template import engines
from django.test import RequestFactory

from djem.middleware import MemoryStorage

BETWEEN_TAG_WHITESPACE_RE = re.compile(r'>\s+<')
EXCESS_WHITESPACE_RE = re.compile(r'\s\s+')


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
        
        request = super(MessagingRequestFactory, self).request(**request)
        
        # Patch the request so it appears as though the
        # djem.middleware.MessageMiddleware is in use, and it is an AJAX request
        request._messages = MemoryStorage(request)
        
        return request


class TemplateRendererMixin(object):
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
