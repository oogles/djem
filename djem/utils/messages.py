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
    
    def request(self, **request):
        
        request = super(MessagingRequestFactory, self).request(**request)
        
        # Patch the request so it appears as though the
        # djem.middleware.MessageMiddleware is in use, and it is an AJAX request
        request._messages = MemoryStorage(request)
        
        return request
