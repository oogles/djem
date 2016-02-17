from django.test import TestCase
from django.contrib.auth import get_user_model

from django_goodies.forms import CommonInfoForm

from .models import StaticTest

class CommonInfoTestForm(CommonInfoForm):
    
    class Meta:
        model = StaticTest
        fields = '__all__'

class CommonInfoFormTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        # This user is not modified during these tests, so no need to
        # refresh_from_db in setUp
        cls.user = get_user_model().objects.create_user('test', 'fakepassword')
    
    def test_bound_init_user(self):
        """
        Test the form correctly stores the given user when instantiating it
        with data (a bound form).
        """
        
        form = CommonInfoTestForm({'test': True}, user=self.user)
        
        self.assertEquals(form.user, self.user)
    
    def test_bound_init_no_user(self):
        """
        Test the form correctly raises a TypeError if no user is given when
        instantiating it with data (a bound form).
        """
        
        with self.assertRaises(TypeError):
            CommonInfoTestForm({'test': True})
    
    def test_unbound_init_user(self):
        """
        Test the form correctly stores the given user when instantiating it
        without data (an unbound form), even though it is not required.
        """
        
        form = CommonInfoTestForm(user=self.user)
        
        self.assertEquals(form.user, self.user)
    
    def test_unbound_init_no_user(self):
        """
        Test the form correctly stores ``None`` if no user is given when
        instantiating it without data (an unbound form).
        """
        
        form = CommonInfoTestForm()
        
        self.assertIsNone(form.user)
    
    def test_save_commit_true(self):
        """
        Test the form saves correctly when ``save`` is called with ``commit=True``
        (or no ``commit`` argument at all).
        """
        
        form = CommonInfoTestForm({'test': True}, user=self.user)
        
        instance = form.save()
        
        # Test correct insertion into database, with appropriate user fields
        self.assertIsNotNone(instance.pk)
        self.assertEquals(instance.user_created_id, self.user.pk)
        self.assertEquals(instance.user_modified_id, self.user.pk)
        
        # Test save_m2m method is inaccessible, as it should be after a
        # commit=True save
        with self.assertRaises(AttributeError):
            form.save_m2m
        
        self.assertNumQueries(1)
    
    def test_save_commit_false(self):
        """
        Test the form behaves correctly but does NOT save when ``save`` is
        called with ``commit=False``.
        """
        
        form = CommonInfoTestForm({'test': True}, user=self.user)
        
        instance = form.save(commit=False)
        
        # Test instance is not saved
        self.assertIsNone(instance.pk)
        
        # Test manual saving works
        instance.save(self.user)
        form.save_m2m()
        
        self.assertIsNotNone(instance.pk)
        self.assertEquals(instance.user_created_id, self.user.pk)
        self.assertEquals(instance.user_modified_id, self.user.pk)
        
        self.assertNumQueries(0)
