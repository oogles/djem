from django.contrib.messages.storage.base import BaseStorage
from django.test import RequestFactory


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
