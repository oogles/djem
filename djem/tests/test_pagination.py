from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage
from django.test import TestCase

from djem.pagination import get_page

from .models import CommonInfoTest


class GetPageTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        user = get_user_model().objects.create_user('test')
        
        for i in range(23):
            CommonInfoTest().save(user)
        
        cls.object_list = CommonInfoTest.objects.order_by('pk')
    
    def test_per_page__none(self):
        
        with self.assertRaises(TypeError):
            get_page(1, self.object_list)
    
    def test_per_page__default(self):
        
        with self.settings(DJEM_DEFAULT_PAGE_LENGTH=10):
            page = get_page(1, self.object_list)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 10)
        self.assertEqual(page.start_index(), 1)
        self.assertEqual(page.end_index(), 10)
        self.assertEqual(page.paginator.count, 23)
        self.assertEqual(page.paginator.num_pages, 3)
    
    def test_per_page__custom(self):
        
        with self.settings(DJEM_DEFAULT_PAGE_LENGTH=10):
            page = get_page(1, self.object_list, 20)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 20)
        self.assertEqual(page.start_index(), 1)
        self.assertEqual(page.end_index(), 20)
        self.assertEqual(page.paginator.count, 23)
        self.assertEqual(page.paginator.num_pages, 2)
    
    def test_page__invalid(self):
        
        page = get_page('fail', self.object_list, 10)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 10)
        self.assertEqual(page.start_index(), 1)
        self.assertEqual(page.end_index(), 10)
        self.assertEqual(page.paginator.count, 23)
        self.assertEqual(page.paginator.num_pages, 3)
    
    def test_page__negative(self):
        
        page = get_page(-1, self.object_list, 10)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 10)
        self.assertEqual(page.start_index(), 1)
        self.assertEqual(page.end_index(), 10)
        self.assertEqual(page.paginator.count, 23)
        self.assertEqual(page.paginator.num_pages, 3)
    
    def test_page__large(self):
        
        page = get_page(10000, self.object_list, 10)
        
        self.assertEqual(page.number, 3)
        self.assertEqual(len(page), 3)
        self.assertEqual(page.start_index(), 21)
        self.assertEqual(page.end_index(), 23)
        self.assertEqual(page.paginator.count, 23)
        self.assertEqual(page.paginator.num_pages, 3)
    
    def test_empty_list__allow_empty_first__page0(self):
        
        page = get_page(0, [], 10)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 0)
        self.assertEqual(page.paginator.count, 0)
        self.assertEqual(page.paginator.num_pages, 1)
    
    def test_empty_list__allow_empty_first__page1(self):
        
        page = get_page(1, [], 10)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 0)
        self.assertEqual(page.paginator.count, 0)
        self.assertEqual(page.paginator.num_pages, 1)
    
    def test_empty_list__allow_empty_first__page2(self):
        
        page = get_page(2, [], 10)
        
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page), 0)
        self.assertEqual(page.paginator.count, 0)
        self.assertEqual(page.paginator.num_pages, 1)
    
    def test_empty_list__deny_empty_first__page0(self):
        
        # Specifically ensure it is not the "That page number is less than 1" error
        with self.assertRaisesMessage(EmptyPage, 'That page contains no results'):
            get_page(0, [], 10, allow_empty_first_page=False)
    
    def test_empty_list__deny_empty_first__page1(self):
        
        # Specifically ensure it is not the "That page number is less than 1" error
        with self.assertRaisesMessage(EmptyPage, 'That page contains no results'):
            get_page(1, [], 10, allow_empty_first_page=False)
    
    def test_empty_list__deny_empty_first__page2(self):
        
        # Specifically ensure it is not the "That page number is less than 1" error
        with self.assertRaisesMessage(EmptyPage, 'That page contains no results'):
            get_page(2, [], 10, allow_empty_first_page=False)
