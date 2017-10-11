from django.contrib.auth import get_user_model
from django.test import TestCase

from djem import get_page

from .app.models import CommonInfoTest


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
