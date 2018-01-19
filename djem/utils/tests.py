from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory


class MessagingRequestFactory(RequestFactory):
    
    def request(self, **request):
        
        request = super(MessagingRequestFactory, self).request(**request)
        
        # Patch the request so it appears as though the
        # django.contrib.messages.middleware.MessageMiddleware is in use (as
        # documented in https://code.djangoproject.com/ticket/17971)
        request.session = 'session'
        request._messages = FallbackStorage(request)
        
        return request
