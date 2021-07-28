from django.conf import settings
from django.contrib.messages.storage import default_storage
from django.contrib.messages.storage.base import BaseStorage


class MemoryStorage(BaseStorage):
    """
    A messages framework storage backend that does not implement any persistent
    storage of the messages added to it. Messages are stored in memory only -
    if they are not read within the same request, they are lost.
    """
    
    def _get(self, *args, **kwargs):
        
        return None, True
    
    def _store(self, messages, response, *args, **kwargs):
        
        return []


class MessageMiddleware:
    """
    Middleware that handles temporary messages, differentiating between those
    added as part of an AJAX request vs those that are not. Different storage
    backends are used for each.
    """
    
    def __init__(self, get_response):
        
        self.get_response = get_response
    
    def __call__(self, request):
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if is_ajax:
            request._messages = MemoryStorage(request)
        else:
            request._messages = default_storage(request)
        
        response = self.get_response(request)
        
        #
        # The following is copied verbatim from Django's own MessageMiddleware
        # (apart from the pragma)
        #
        
        # A higher middleware layer may return a request which does not contain
        # messages storage, so make no assumption that it will be there.
        if hasattr(request, '_messages'):  # pragma: no cover
            unstored_messages = request._messages.update(response)
            if unstored_messages and settings.DEBUG:
                raise ValueError('Not all temporary messages could be stored.')
        
        return response
