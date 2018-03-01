import json

from django.contrib import messages
from django.template.defaultfilters import mark_safe
from django.test import TestCase

from djem.ajax import AjaxResponse
from djem.utils.tests import MessagingRequestFactory


class AjaxResponseTestCase(TestCase):
    
    def setUp(self):
        
        self.factory = MessagingRequestFactory()
    
    def test_response__no_args(self):
        """
        Test that a TypeError is raised when trying to instantiate AjaxResponse
        with no arguments - the "request" argument is required.
        """
        
        def view(r):
            
            return AjaxResponse()
        
        request = self.factory.get('/test/')
        
        with self.assertRaises(TypeError):
            view(request)
    
    def test_response__request_only(self):
        """
        Test that AjaxResponse correctly instantiates when only given the
        "request" argument, and simply contains an empty response body.
        """
        
        def view(r):
            
            return AjaxResponse(r)
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode()), {})
    
    def test_response__data(self):
        """
        Test that AjaxResponse correctly includes the given data in the response
        body.
        """
        
        def view(r):
            
            return AjaxResponse(r, {'test': 'test'})
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(data['test'], 'test')
    
    def test_response__bad_data(self):
        """
        Test that a TypeError is raised when trying to instantiate AjaxResponse
        with a non-dict "data" argument.
        """
        
        def view(r):
            
            return AjaxResponse(r, ['test', 'test'])
        
        request = self.factory.get('/test/')
        
        with self.assertRaises(TypeError):
            view(request)
    
    def test_response__success__true(self):
        """
        Test that AjaxResponse correctly includes "success=True" in the response
        body when no other data is given.
        """
        
        def view(r):
            
            return AjaxResponse(r, success=True)
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertIs(data['success'], True)
    
    def test_response__success__false(self):
        """
        Test that AjaxResponse correctly includes the given data in the response
        body.
        """
        
        def view(r):
            
            return AjaxResponse(r, success=False)
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertIs(data['success'], False)
    
    def test_response__success__dumb(self):
        """
        Test that AjaxResponse correctly includes a boolean success flag in the
        response body when the success argument is given as a non-boolean value.
        """
        
        def view(r):
            
            return AjaxResponse(r, success='dumb')
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertIs(data['success'], True)
    
    def test_response__success__data(self):
        """
        Test that AjaxResponse correctly includes a boolean success flag in the
        response body when other data is also provided.
        """
        
        def view(r):
            
            return AjaxResponse(r, {'test': 'test'}, success=True)
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 2)
        self.assertEqual(data['test'], 'test')
        self.assertIs(data['success'], True)
    
    def test_response__messages(self):
        """
        Test that AjaxResponse correctly includes messages stored by the Django
        messages framework in the response body.
        """
        
        def view(r):
            
            messages.success(request, 'This is a success message.')
            messages.error(request, 'This is an error message.')
            messages.add_message(request, messages.INFO, 'This is an info message.', extra_tags='special')
            
            return AjaxResponse(r)
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data['messages']), 3)
        
        success = data['messages'][0]
        self.assertEqual(success['message'], 'This is a success message.')
        self.assertEqual(success['tags'], 'success')
        
        error = data['messages'][1]
        self.assertEqual(error['message'], 'This is an error message.')
        self.assertEqual(error['tags'], 'error')
        
        info = data['messages'][2]
        self.assertEqual(info['message'], 'This is an info message.')
        self.assertEqual(info['tags'], 'special info')
    
    def test_response__messages__xss(self):
        """
        Test that AjaxResponse escapes messages added to the response body from
        Django's messages framework.
        """
        
        def view(r):
            
            messages.error(r, 'This is a message <em>with bad HTML</em>.')
            messages.success(r, mark_safe('This is a message <em>with safe HTML</em>.'))
            
            return AjaxResponse(r)
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data['messages']), 2)
        
        self.assertEqual(data['messages'][0]['message'], 'This is a message &lt;em&gt;with bad HTML&lt;/em&gt;.')
        self.assertEqual(data['messages'][1]['message'], 'This is a message <em>with safe HTML</em>.')
    
    def test_response__messages__data(self):
        """
        Test that AjaxResponse correctly includes messages stored by the Django
        messages framework in the response body when other data is also provided.
        """
        
        def view(r):
            
            messages.success(request, 'This is a success message.')
            
            return AjaxResponse(r, {'test': 'test'})
        
        request = self.factory.get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 2)
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['test'], 'test')
        
        success = data['messages'][0]
        self.assertEqual(success['message'], 'This is a success message.')
        self.assertEqual(success['tags'], 'success')
