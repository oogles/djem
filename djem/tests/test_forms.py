import warnings

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase

from djem.forms import AuditableForm, CommonInfoForm, TimeZoneField, UserSavable
from djem.utils.dt import TIMEZONE_CHOICES, TimeZoneHelper

from .models import StaticTest, TimeZoneTest


class UserSavableTestForm(UserSavable, forms.ModelForm):
    
    def __init__(self, *args, user=None, **kwargs):
        
        self.user = user
        
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = StaticTest
        fields = '__all__'


class AuditableFormTestForm(AuditableForm):
    
    class Meta:
        model = StaticTest
        fields = '__all__'


class TimeZoneFieldTestForm1(forms.ModelForm):
    
    class Meta:
        model = TimeZoneTest
        fields = ['timezone']


class TimeZoneFieldTestForm2(forms.Form):
    
    # Manually defined field
    timezone = TimeZoneField()


class TimeZoneFieldTestForm3(forms.Form):
    
    # Manually defined field, not required
    timezone = TimeZoneField(required=False)


class TimeZoneFieldTestForm4(forms.Form):
    
    # Manually defined field with custom choices
    timezone = TimeZoneField(choices=TIMEZONE_CHOICES[:10])


class UserSavableTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        cls.user = get_user_model().objects.create_user('test')
    
    def test_save_commit__true(self):
        """
        Test the form saves correctly when ``save`` is called with ``commit=True``
        (or no ``commit`` argument at all).
        """
        
        form = UserSavableTestForm({'test': True}, user=self.user)
        
        with self.assertNumQueries(1):
            instance = form.save()
        
        # Test correct insertion into database, with appropriate user fields
        self.assertIsNotNone(instance.pk)
        self.assertEqual(instance.user_created_id, self.user.pk)
        self.assertEqual(instance.user_modified_id, self.user.pk)
        
        # Test save_m2m method is inaccessible, as it should be after a
        # commit=True save
        with self.assertRaises(AttributeError):
            form.save_m2m
    
    def test_save_commit__false(self):
        """
        Test the form behaves correctly but does NOT save when ``save`` is
        called with ``commit=False``.
        """
        
        form = UserSavableTestForm({'test': True}, user=self.user)
        
        with self.assertNumQueries(0):
            instance = form.save(commit=False)
        
        # Test instance is not saved
        self.assertIsNone(instance.pk)
        
        # Test manual saving works
        instance.save(self.user)
        form.save_m2m()
        
        self.assertIsNotNone(instance.pk)
        self.assertEqual(instance.user_created_id, self.user.pk)
        self.assertEqual(instance.user_modified_id, self.user.pk)


class AuditableFormTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        cls.user = get_user_model().objects.create_user('test')
    
    def test_bound_init__user(self):
        """
        Test the form correctly stores the given user when instantiating it
        with data (a bound form).
        """
        
        form = AuditableFormTestForm({'test': True}, user=self.user)
        
        self.assertEqual(form.user, self.user)
    
    def test_bound_init__no_user(self):
        """
        Test the form correctly raises a TypeError if no user is given when
        instantiating it with data (a bound form).
        """
        
        with self.assertRaises(TypeError):
            AuditableFormTestForm({'test': True})
    
    def test_unbound_init__user(self):
        """
        Test the form correctly stores the given user when instantiating it
        without data (an unbound form), even though it is not required.
        """
        
        form = AuditableFormTestForm(user=self.user)
        
        self.assertEqual(form.user, self.user)
    
    def test_unbound_init__no_user(self):
        """
        Test the form correctly stores ``None`` if no user is given when
        instantiating it without data (an unbound form).
        """
        
        form = AuditableFormTestForm()
        
        self.assertIsNone(form.user)


class CommonInfoFormTestCase(TestCase):
    
    def test_deprecation_warning(self):
        
        class TestForm(CommonInfoForm):
            
            class Meta:
                model = StaticTest
                fields = '__all__'
        
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered
            warnings.simplefilter("always")
            
            TestForm()
            
            self.assertEqual(len(w), 1)
            self.assertIs(w[-1].category, DeprecationWarning)
            self.assertIn(
                'Use of CommonInfoForm is deprecated, use AuditableForm instead',
                str(w[-1].message)
            )


class TimeZoneFieldFormTestCase(TestCase):
    
    def test_submit__modelform_valid(self):
        """
        Test a ModelForm based on a Model with a TimeZoneField correctly
        accepts a valid submitted timezone string and cleans it to the correct
        TimeZoneHelper.
        """
        
        form = TimeZoneFieldTestForm1({'timezone': 'Australia/Sydney'})
        
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data['timezone'], TimeZoneHelper)
        self.assertEqual(form.cleaned_data['timezone'].name, 'Australia/Sydney')
    
    def test_submit__modelform_invalid(self):
        """
        Test a ModelForm based on a Model with a TimeZoneField correctly
        accepts an invalid submitted timezone string and generates the
        appropriate error.
        """
        
        form = TimeZoneFieldTestForm1({'timezone': 'fail'})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['timezone'], [
            'Select a valid choice. fail is not one of the available choices.'
        ])
    
    def test_submit__form__valid(self):
        """
        Test a Form with a TimeZoneField correctly accepts a valid submitted
        timezone string and cleans it to the correct TimeZoneHelper.
        """
        
        form = TimeZoneFieldTestForm2({'timezone': 'Australia/Sydney'})
        
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data['timezone'], TimeZoneHelper)
        self.assertEqual(form.cleaned_data['timezone'].name, 'Australia/Sydney')
    
    def test_submit__form__invalid(self):
        """
        Test a Form with a TimeZoneField correctly accepts an invalid submitted
        timezone string and generates the appropriate error.
        """
        
        form = TimeZoneFieldTestForm2({'timezone': 'fail'})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['timezone'], [
            'Select a valid choice. fail is not one of the available choices.'
        ])
    
    def test_submit__form__empty_valid__no_input(self):
        """
        Test a Form with a non-required TimeZoneField correctly accepts no input
        for the timezone value and cleans it to an empty string.
        """
        
        form = TimeZoneFieldTestForm3({})
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['timezone'], '')
    
    def test_submit__form__empty_valid__blank_string(self):
        """
        Test a Form with a non-required TimeZoneField correctly accepts an empty
        string as input for the timezone value and cleans it to an empty string.
        """
        
        form = TimeZoneFieldTestForm3({'timezone': ''})
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['timezone'], '')
    
    def test_submit__form__empty_valid__none(self):
        """
        Test a Form with a non-required TimeZoneField correctly accepts None as
        input for the timezone value and cleans it to an empty string.
        """
        
        form = TimeZoneFieldTestForm3({'timezone': None})
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['timezone'], '')
    
    def test_submit__form__empty_invalid__no_input(self):
        """
        Test a Form with a required TimeZoneField does not accept no input for
        the timezone value and generates the appropriate error.
        """
        
        form = TimeZoneFieldTestForm2({})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['timezone'], [
            'This field is required.'
        ])
    
    def test_submit__form__empty_invalid__blank_string(self):
        """
        Test a Form with a required TimeZoneField does not accept an empty
        string as input for the timezone value and generates the appropriate error.
        """
        
        form = TimeZoneFieldTestForm2({'timezone': ''})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['timezone'], [
            'This field is required.'
        ])
    
    def test_submit__form__empty_invalid__none(self):
        """
        Test a Form with a required TimeZoneField does not accept None as input
        for the timezone value and generates the appropriate error.
        """
        
        form = TimeZoneFieldTestForm2({'timezone': None})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['timezone'], [
            'This field is required.'
        ])
    
    def test_custom_choices__valid(self):
        """
        Test a Form with a TimeZoneField defined with a custom list of choices
        correctly accepts a valid submitted timezone string and cleans it to
        the correct TimeZoneHelper.
        """
        
        tz = TIMEZONE_CHOICES[0][0]
        
        form = TimeZoneFieldTestForm4({'timezone': tz})
        
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data['timezone'], TimeZoneHelper)
        self.assertEqual(form.cleaned_data['timezone'].name, tz)
    
    def test_custom_choices__invalid(self):
        """
        Test a Form with a TimeZoneField defined with a custom list of choices
        correctly accepts an invalid submitted timezone string and generates
        the appropriate error.
        """
        
        form = TimeZoneFieldTestForm4({'timezone': 'Australia/Sydney'})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['timezone'], [
            'Select a valid choice. Australia/Sydney is not one of the available choices.'
        ])
