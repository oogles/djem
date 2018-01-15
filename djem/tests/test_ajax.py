from django.urls import reverse
from django.test import TestCase


class AjaxResponseTestCase(TestCase):
    
    def test_response__no_args(self):
        """
        Test that a TypeError is raised when trying to instantiate AjaxResponse
        with no arguments - the "request" argument is required.
        """
        
        with self.assertRaises(TypeError):
            self.client.get(reverse('ajax__no_args'))
    
    def test_response__request_only(self):
        """
        Test that AjaxResponse correctly instantiates when only given the
        "request" argument, and simply contains an empty response body.
        """
        
        response = self.client.get(reverse('ajax__request_only'))
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json(), {})
    
    def test_response__data(self):
        """
        Test that AjaxResponse correctly includes the given data in the response
        body.
        """
        
        response = self.client.get(reverse('ajax__data'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 1)
        self.assertEquals(data['test'], 'test')
    
    def test_response__bad_data(self):
        """
        Test that a TypeError is raised when trying to instantiate AjaxResponse
        with a non-dict "data" argument.
        """
        
        with self.assertRaises(TypeError):
            self.client.get(reverse('ajax__bad_data'))
    
    def test_response__success__true(self):
        """
        Test that AjaxResponse correctly includes "success=True" in the response
        body when no other data is given.
        """
        
        response = self.client.get(reverse('ajax__success__true'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 1)
        self.assertIs(data['success'], True)
    
    def test_response__success__false(self):
        """
        Test that AjaxResponse correctly includes the given data in the response
        body.
        """
        
        response = self.client.get(reverse('ajax__success__false'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 1)
        self.assertIs(data['success'], False)
    
    def test_response__success__dumb(self):
        """
        Test that AjaxResponse correctly includes a boolean success flag in the
        response body when the success argument is given as a non-boolean value.
        """
        
        response = self.client.get(reverse('ajax__success__dumb'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 1)
        self.assertIs(data['success'], True)
    
    def test_response__success__data(self):
        """
        Test that AjaxResponse correctly includes a boolean success flag in the
        response body when other data is also provided.
        """
        
        response = self.client.get(reverse('ajax__success__data'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 2)
        self.assertEquals(data['test'], 'test')
        self.assertIs(data['success'], True)
    
    def test_response__messages(self):
        """
        Test that AjaxResponse correctly includes messages stored by the Django
        messages framework in the response body.
        """
        
        response = self.client.get(reverse('ajax__messages'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 1)
        self.assertEquals(len(data['messages']), 3)
        
        success = data['messages'][0]
        self.assertEquals(success['message'], 'This is a success message.')
        self.assertEquals(success['tags'], 'success')
        
        error = data['messages'][1]
        self.assertEquals(error['message'], 'This is an error message.')
        self.assertEquals(error['tags'], 'error')
        
        info = data['messages'][2]
        self.assertEquals(info['message'], 'This is an info message.')
        self.assertEquals(info['tags'], 'special info')
    
    def test_response__messages__data(self):
        """
        Test that AjaxResponse correctly includes messages stored by the Django
        messages framework in the response body when other data is also provided.
        """
        
        response = self.client.get(reverse('ajax__messages__data'))
        
        self.assertEquals(response.status_code, 200)
        
        data = response.json()
        self.assertEquals(len(data), 2)
        self.assertEquals(len(data['messages']), 1)
        self.assertEquals(data['test'], 'test')
        
        success = data['messages'][0]
        self.assertEquals(success['message'], 'This is a success message.')
        self.assertEquals(success['tags'], 'success')
