from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from djem import get_page

from .app.models import CommonInfoTest


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


class GetPageTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        user = get_user_model().objects.create_user('test')
        
        for i in range(23):
            CommonInfoTest().save(user)
        
        cls.object_list = CommonInfoTest.objects.all()
    
    def test_per_page__none(self):
        
        with self.assertRaises(TypeError):
            get_page(1, self.object_list)
    
    def test_per_page__default(self):
        
        with self.settings(DJEM_DEFAULT_PAGE_LENGTH=10):
            page = get_page(1, self.object_list)
        
        self.assertEquals(page.number, 1)
        self.assertEquals(len(page), 10)
        self.assertEquals(page.start_index(), 1)
        self.assertEquals(page.end_index(), 10)
        self.assertEquals(page.paginator.count, 23)
        self.assertEquals(page.paginator.num_pages, 3)
    
    def test_per_page__custom(self):
        
        with self.settings(DJEM_DEFAULT_PAGE_LENGTH=10):
            page = get_page(1, self.object_list, 20)
        
        self.assertEquals(page.number, 1)
        self.assertEquals(len(page), 20)
        self.assertEquals(page.start_index(), 1)
        self.assertEquals(page.end_index(), 20)
        self.assertEquals(page.paginator.count, 23)
        self.assertEquals(page.paginator.num_pages, 2)
    
    def test_page__invalid(self):
        
        page = get_page('fail', self.object_list, 10)
        
        self.assertEquals(page.number, 1)
        self.assertEquals(len(page), 10)
        self.assertEquals(page.start_index(), 1)
        self.assertEquals(page.end_index(), 10)
        self.assertEquals(page.paginator.count, 23)
        self.assertEquals(page.paginator.num_pages, 3)
    
    def test_page__negative(self):
        
        page = get_page(-1, self.object_list, 10)
        
        self.assertEquals(page.number, 1)
        self.assertEquals(len(page), 10)
        self.assertEquals(page.start_index(), 1)
        self.assertEquals(page.end_index(), 10)
        self.assertEquals(page.paginator.count, 23)
        self.assertEquals(page.paginator.num_pages, 3)
    
    def test_page__large(self):
        
        page = get_page(10000, self.object_list, 10)
        
        self.assertEquals(page.number, 3)
        self.assertEquals(len(page), 3)
        self.assertEquals(page.start_index(), 21)
        self.assertEquals(page.end_index(), 23)
        self.assertEquals(page.paginator.count, 23)
        self.assertEquals(page.paginator.num_pages, 3)
