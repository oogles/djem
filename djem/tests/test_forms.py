from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase

from djem.forms import CommonInfoForm, TimeZoneField
from djem.utils.dt import TIMEZONE_CHOICES, TimeZoneHelper

from .models import StaticTest, TimeZoneTest


class CommonInfoTestForm(CommonInfoForm):
    
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


class CommonInfoFormTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        # This user is not modified during these tests, so no need to
        # refresh_from_db in setUp
        cls.user = get_user_model().objects.create_user('test', 'fakepassword')
    
    def test_bound_init__user(self):
        """
        Test the form correctly stores the given user when instantiating it
        with data (a bound form).
        """
        
        form = CommonInfoTestForm({'test': True}, user=self.user)
        
        self.assertEqual(form.user, self.user)
    
    def test_bound_init__no_user(self):
        """
        Test the form correctly raises a TypeError if no user is given when
        instantiating it with data (a bound form).
        """
        
        with self.assertRaises(TypeError):
            CommonInfoTestForm({'test': True})
    
    def test_unbound_init__user(self):
        """
        Test the form correctly stores the given user when instantiating it
        without data (an unbound form), even though it is not required.
        """
        
        form = CommonInfoTestForm(user=self.user)
        
        self.assertEqual(form.user, self.user)
    
    def test_unbound_init__no_user(self):
        """
        Test the form correctly stores ``None`` if no user is given when
        instantiating it without data (an unbound form).
        """
        
        form = CommonInfoTestForm()
        
        self.assertIsNone(form.user)
    
    def test_save_commit__true(self):
        """
        Test the form saves correctly when ``save`` is called with ``commit=True``
        (or no ``commit`` argument at all).
        """
        
        form = CommonInfoTestForm({'test': True}, user=self.user)
        
        instance = form.save()
        
        # Test correct insertion into database, with appropriate user fields
        self.assertIsNotNone(instance.pk)
        self.assertEqual(instance.user_created_id, self.user.pk)
        self.assertEqual(instance.user_modified_id, self.user.pk)
        
        # Test save_m2m method is inaccessible, as it should be after a
        # commit=True save
        with self.assertRaises(AttributeError):
            form.save_m2m
        
        self.assertNumQueries(1)
    
    def test_save_commit__false(self):
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
        self.assertEqual(instance.user_created_id, self.user.pk)
        self.assertEqual(instance.user_modified_id, self.user.pk)
        
        self.assertNumQueries(0)


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
        self.assertEqual(form.cleaned_data['timezone'].tz.zone, 'Australia/Sydney')
    
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
        self.assertEqual(form.cleaned_data['timezone'].tz.zone, 'Australia/Sydney')
    
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
        self.assertEqual(form.cleaned_data['timezone'].tz.zone, tz)
    
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
