from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib import messages
from django.contrib.messages import constants
from django.http import HttpRequest, HttpResponse
from django.test import Client, TestCase, override_settings

from djem.middleware import MemoryStorage


def add_message_view(request):
    
    msg = request.GET['msg']
    messages.info(request, msg)
    
    if request.is_ajax():
        prefix = 'AJAX'
    else:
        prefix = 'STANDARD'
    
    return HttpResponse('{0}: no messages'.format(prefix))


def add_read_message_view(request):
    
    msg = request.GET['msg']
    messages.info(request, msg)
    
    content = ', '.join([msg.message for msg in messages.get_messages(request)])
    
    if request.is_ajax():
        prefix = 'AJAX'
    else:
        prefix = 'STANDARD'
    
    return HttpResponse('{0}: {1}'.format(prefix, content))


urlpatterns = [
    url(r'^messages/add/$', add_message_view),
    url(r'^messages/add/read/$', add_read_message_view),
]


djem_middleware_settings = override_settings(
    ROOT_URLCONF='djem.tests.test_middleware',
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'djem.middleware.MessageMiddleware'
    ]
)

django_middleware_settings = override_settings(
    ROOT_URLCONF='djem.tests.test_middleware',
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware'
    ]
)


class MemoryStorageTestCase(TestCase):
    
    def test_add(self):
        """
        Test messages can be added and retrieved as expected.
        """
        
        # Create a message store with a fake request instance
        messages = MemoryStorage(HttpRequest())
        
        self.assertEqual(len(messages), 0)
        
        messages.add(constants.INFO, 'Test message')
        self.assertEqual(len(messages), 1)
        
        messages.add(constants.INFO, 'Another test message')
        self.assertEqual(len(messages), 2)
        
        # Read the message store
        message_list = list(messages)
        
        messages.add(constants.INFO, 'A third test message')
        
        self.assertEqual(len(message_list), 2)
        self.assertEqual(len(messages), 3)


class MessageMiddlewareTestCase(TestCase):
    
    def setUp(self):
        
        self.client = Client()
    
    @djem_middleware_settings
    def test_standard_request(self):
        """
        Test that messages added via the message framework, on a standard
        request, can be read back when using djem's MessageMiddleware.
        """
        
        response = self.client.get(
            '/messages/add/read/',
            {'msg': 'test message'}
        )
        
        self.assertEqual(response.content, b'STANDARD: test message')
    
    @djem_middleware_settings
    def test_ajax_request(self):
        """
        Test that messages added via the message framework, on an AJAX
        request, can be read back when using djem's MessageMiddleware.
        """
        
        response = self.client.get(
            '/messages/add/read/',
            {'msg': 'test message'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.content, b'AJAX: test message')
    
    @djem_middleware_settings
    def test_mixed_requests(self):
        """
        Test that messages added on standard requests and AJAX requests use
        different stores and do not interfere with each other when using djem's
        MessageMiddleware.
        """
        
        # Start with a standard request that adds a message, but doesn't read
        # back the message store
        response = self.client.get(
            '/messages/add/',
            {'msg': 'first standard message'}
        )
        
        self.assertEqual(response.content, b'STANDARD: no messages')
        
        # Next, trigger an AJAX request that adds a message, but also doesn't
        # read back the message store. This message should be lost once the
        # request is completed.
        response = self.client.get(
            '/messages/add/',
            {'msg': 'lost ajax message'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.content, b'AJAX: no messages')
        
        # Then trigger an AJAX request that adds a message and does read back
        # the message store - it should only see the message it added, not
        # either of the two previous messages.
        response = self.client.get(
            '/messages/add/read/',
            {'msg': 'ajax message'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.content, b'AJAX: ajax message')
        
        # Finally, trigger another standard request that adds a message and
        # reads back the message store - it should see the two messages added
        # as part of standard requests, and not those added in the AJAX request
        response = self.client.get(
            '/messages/add/read/',
            {'msg': 'second standard message'}
        )
        
        self.assertEqual(response.content, b'STANDARD: first standard message, second standard message')
    
    @django_middleware_settings
    def test_django_mixed_requests(self):
        """
        Test that messages added on standard requests and AJAX requests DO
        interfere with each other when using Django's MessageMiddleware.
        """
        
        # Start with a standard request that adds a message, but doesn't read
        # back the message store
        response = self.client.get(
            '/messages/add/',
            {'msg': 'first standard message'}
        )
        
        self.assertEqual(response.content, b'STANDARD: no messages')
        
        # Then trigger an AJAX request that adds a message and does read back
        # the message store - it sees all messages
        response = self.client.get(
            '/messages/add/read/',
            {'msg': 'ajax message'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.content, b'AJAX: first standard message, ajax message')
        
        # Finally, trigger another standard request that adds a message and
        # reads back the message store - it only sees its own message, since
        # the others were consumed by the intervening AJAX request
        response = self.client.get(
            '/messages/add/read/',
            {'msg': 'second standard message'}
        )
        
        self.assertEqual(response.content, b'STANDARD: second standard message')
