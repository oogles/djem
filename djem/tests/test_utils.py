import datetime
import warnings
from copy import deepcopy
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.apps import apps
from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from djem import UNDEFINED
from djem.utils.dev import Developer
from djem.utils.dt import TimeZoneHelper
from djem.utils.tests import setup_test_app


class UndefinedTestCase(SimpleTestCase):
    
    def test_falsey(self):
        
        self.assertFalse(UNDEFINED)
    
    def test_print(self):
        
        self.assertEqual(str(UNDEFINED), '<undefined>')
    
    def test_deepcopy__direct(self):
        
        clone = deepcopy(UNDEFINED)
        
        self.assertIs(clone, UNDEFINED)
    
    def test_deepcopy__indirect(self):
        
        val = {'value': UNDEFINED}
        clone = deepcopy(val)
        
        self.assertIs(clone['value'], UNDEFINED)


class DeveloperTestCase(SimpleTestCase):
    """
    Tests for the Developer utility class.
    """
    
    @override_settings(DJEM_DEV_USER={'pk': 1})
    def test_user__explicit_kwargs(self):
        """
        Test the `user` property when explicit lookup kwargs are provided.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            user = dev.user
            
            mock_get_user_model.return_value.objects.get.assert_called_once_with(username='testuser')
        
        self.assertIs(user, mock_user)
    
    @override_settings(DJEM_DEV_USER={'pk': 1})
    def test_user__settings(self):
        """
        Test the `user` property when no explicit lookup kwargs are provided,
        but the `DJEM_DEV_USER` setting is defined.
        """
        
        dev = Developer()
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            user = dev.user
            
            mock_get_user_model.return_value.objects.get.assert_called_once_with(pk=1)
        
        self.assertIs(user, mock_user)
    
    def test_user__no_kwargs(self):
        """
        Test the `user` property when no lookup kwargs are provided, either
        explicitly or via the `DJEM_DEV_USER` setting.
        """
        
        dev = Developer()
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            user = dev.user
            
            # Should be called without arguments - would error in actual use
            mock_get_user_model.return_value.objects.get.assert_called_once_with()
        
        self.assertIs(user, mock_user)
    
    def test_user__cached(self):
        """
        Test that the `user` property is cached after first access.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            user1 = dev.user
            user2 = dev.user
            
            # Should only be called once due to caching
            mock_get_user_model.return_value.objects.get.assert_called_once()
        
        self.assertIs(user1, user2)
    
    def test_be_awesome(self):
        """
        Test the be_awesome() method. It should set the fields defined by the
        `awesome` class attribute.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            dev.be_awesome()
        
        self.assertTrue(mock_user.is_staff)
        self.assertTrue(mock_user.is_superuser)
        mock_user.save.assert_called_once()
    
    def test_be_awesome__customised(self):
        """
        Test the be_awesome() method on a subclass that customises the `awesome`
        class attribute. It should set the fields defined by the customisations.
        """
        
        class CustomDeveloper(Developer):
            
            awesome = {
                'is_superuser': True,
                'is_developer': True,
                'custom_field': 'awesome_value'
            }
        
        dev = CustomDeveloper(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            dev.be_awesome()
        
        self.assertTrue(mock_user.is_superuser)
        self.assertTrue(mock_user.is_developer)
        self.assertEqual(mock_user.custom_field, 'awesome_value')
        mock_user.save.assert_called_once()
    
    def test_be_boring(self):
        """
        Test the be_boring() method. It should set the fields defined by the
        `boring` class attribute.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            dev.be_boring()
        
        self.assertFalse(mock_user.is_staff)
        self.assertFalse(mock_user.is_superuser)
        mock_user.save.assert_called_once()
    
    def test_be_boring__customised(self):
        """
        Test the be_boring() method on a subclass that customises the `boring`
        class attribute. It should set the fields defined by the customisations.
        """
        
        class CustomDeveloper(Developer):
            
            boring = {
                'is_superuser': False,
                'is_developer': False,
                'custom_field': 'boring_value'
            }
        
        dev = CustomDeveloper(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            dev.be_boring()
        
        self.assertFalse(mock_user.is_superuser)
        self.assertFalse(mock_user.is_developer)
        self.assertEqual(mock_user.custom_field, 'boring_value')
        mock_user.save.assert_called_once()
    
    def test_no_super(self):
        """
        Test the no_super() method. It should set `is_superuser` to False.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            dev.no_super()
        
        # Only `is_superuser` should be changed
        self.assertFalse(mock_user.is_superuser)
        self.assertTrue(mock_user.is_staff)
        mock_user.save.assert_called_once_with(update_fields=('is_superuser',))
    
    def test_no_staff(self):
        """
        Test the no_staff() method. It should set `is_staff` to False.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            dev.no_staff()
        
        # Only `is_staff` should be changed
        self.assertFalse(mock_user.is_staff)
        self.assertTrue(mock_user.is_superuser)
        mock_user.save.assert_called_once_with(update_fields=('is_staff',))
    
    def test_add_permissions(self):
        """
        Test the add_permissions() method. It should add the specified
        permissions to the user.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        perm1 = MagicMock()
        perm2 = MagicMock()
        perm3 = MagicMock()
        
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            with patch('djem.utils.dev.Permission') as mock_permission:
                mock_permission.objects.filter.return_value = [perm1, perm2, perm3]
                
                dev.add_permissions('add_mymodel', 'change_mymodel', 'delete_mymodel')
                
                mock_permission.objects.filter.assert_called_once_with(
                    codename__in=('add_mymodel', 'change_mymodel', 'delete_mymodel')
                )
            
            mock_user.user_permissions.add.assert_any_call(perm1)
            mock_user.user_permissions.add.assert_any_call(perm2)
            mock_user.user_permissions.add.assert_any_call(perm3)
    
    def test_remove_permissions(self):
        """
        Test the remove_permissions() method. It should remove the specified
        permissions from the user.
        """
        
        dev = Developer(username='testuser')
        
        mock_user = MagicMock()
        perm1 = MagicMock()
        perm2 = MagicMock()
        perm3 = MagicMock()
        
        with patch('djem.utils.dev.get_user_model') as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_user
            
            with patch('djem.utils.dev.Permission') as mock_permission:
                mock_permission.objects.filter.return_value = [perm1, perm2, perm3]
                
                dev.remove_permissions('add_mymodel', 'change_mymodel', 'delete_mymodel')
                
                mock_permission.objects.filter.assert_called_once_with(
                    codename__in=('add_mymodel', 'change_mymodel', 'delete_mymodel')
                )
            
            mock_user.user_permissions.remove.assert_any_call(perm1)
            mock_user.user_permissions.remove.assert_any_call(perm2)
            mock_user.user_permissions.remove.assert_any_call(perm3)


class TimeZoneHelperTestCase(SimpleTestCase):
    
    def test_init__good_string(self):
        """
        Test constructing a TimeZoneHelper object with a valid timezone string.
        """
        
        helper = TimeZoneHelper('Australia/Sydney')
        
        self.assertEqual(helper.tz.key, 'Australia/Sydney')
    
    def test_init__bad_string(self):
        """
        Test constructing a TimeZoneHelper object with an invalid timezone string.
        """
        
        with self.assertRaises(ZoneInfoNotFoundError):
            TimeZoneHelper('fail')
    
    def test_init__utc(self):
        """
        Test constructing a TimeZoneHelper object with the UTC singleton.
        """
        
        tz = datetime.timezone.utc
        helper = TimeZoneHelper(tz)
        
        self.assertIs(helper.tz, tz)
    
    def test_init__timezone(self):
        """
        Test constructing a TimeZoneHelper object with a valid ZoneInfo
        instance.
        """
        
        tz = ZoneInfo('Australia/Sydney')
        helper = TimeZoneHelper(tz)
        
        self.assertIs(helper.tz, tz)
    
    def test_name(self):
        """
        Test the TimeZoneHelper ``name`` property for several different
        timezones.
        """
        
        self.assertEqual(TimeZoneHelper(datetime.timezone.utc).name, 'UTC')
        self.assertEqual(TimeZoneHelper('Australia/Sydney').name, 'Australia/Sydney')
        self.assertEqual(TimeZoneHelper('US/Eastern').name, 'US/Eastern')
    
    def test_now__utc(self):
        """
        Test the TimeZoneHelper ``now`` method, using the UTC timezone.
        """
        
        now = timezone.now()
        helper_now = TimeZoneHelper(datetime.timezone.utc).now()
        
        self.assertAlmostEqual(helper_now, now, delta=datetime.timedelta(seconds=1))
    
    def test_now__local(self):
        """
        Test the TimeZoneHelper ``now`` method, using a local timezone.
        """
        
        now = timezone.now()
        helper_now = TimeZoneHelper('Australia/Sydney').now()
        local_now = now.astimezone(ZoneInfo('Australia/Sydney'))
        
        self.assertAlmostEqual(helper_now, local_now, delta=datetime.timedelta(seconds=1))
    
    def test_today__utc(self):
        """
        Test the TimeZoneHelper ``today`` method, using the UTC timezone.
        NOTE: This test is subject to some inaccuracy if run at the precise
        moment that caused the two compared datetimes to generate on either
        side of a day interval.
        """
        
        # It would be pretty unlucky for these two datetimes to generate
        # either side of a day interval.
        today = timezone.now().date()
        helper_today = TimeZoneHelper(datetime.timezone.utc).today()
        
        self.assertEqual(helper_today, today)
    
    def test_today__local(self):
        """
        Test the TimeZoneHelper ``today`` method, using a local timezone.
        NOTE: This test is subject to some inaccuracy if run at the precise
        moment that caused the two compared datetimes to generate on either
        side of a day interval.
        """
        
        # It would be pretty unlucky for these two datetimes to generate
        # either side of a day interval.
        now = timezone.now()
        helper_today = TimeZoneHelper('Australia/Sydney').today()
        local_today = now.astimezone(ZoneInfo('Australia/Sydney')).date()
        
        self.assertEqual(helper_today, local_today)
    
    def test_stringify(self):
        """
        Test coercing TimeZoneHelper to a string.
        """
        
        self.assertEqual(str(TimeZoneHelper(datetime.timezone.utc)), 'UTC')
        self.assertEqual(str(TimeZoneHelper('Australia/Sydney')), 'Australia/Sydney')
        self.assertEqual(str(TimeZoneHelper('US/Eastern')), 'US/Eastern')


class SetupTestAppTestCase(SimpleTestCase):
    
    # Use a package *outside* the tests package, since djem's tests themselves
    # make use of setup_test_app()
    package = 'djem.utils'
    
    def test_explicit_label(self):
        """
        Test when an explicit app label is provided. The provided label should
        be used directly.
        """
        
        self.assertNotIn('__test_label__', apps.app_configs)
        setup_test_app(self.package, '__test_label__')
        self.assertIn('__test_label__', apps.app_configs)
        
        # Uninstall the app again to avoid polluting other tests
        apps.app_configs.pop('__test_label__')
    
    def test_explicit_label__duplicate(self):
        """
        Test when called multiple times with an explicit app label provided.
        The second attempt should have no effect.
        """
        
        n = len(apps.app_configs)
        
        setup_test_app(self.package, '__test_label__')
        self.assertEqual(len(apps.app_configs), n + 1)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')  # ensure all warnings are triggered
            
            setup_test_app(self.package, '__test_label__')
            
            self.assertEqual(len(w), 1)
            self.assertTrue(w[0].message, 'Attempted setup of duplicate test app "__test_label__".')
            self.assertTrue(w[0].category, RuntimeWarning)
        
        self.assertEqual(len(apps.app_configs), n + 1)
        
        # Uninstall the app again to avoid polluting other tests
        apps.app_configs.pop('__test_label__')
    
    def test_implicit_label(self):
        """
        Test when no explicit app label is provided. The label of the
        containing app, suffixed with "_tests", should be used.
        """
        
        self.assertNotIn('djem_tests', apps.app_configs)
        setup_test_app(self.package)
        self.assertIn('djem_tests', apps.app_configs)
        
        # Uninstall the app again to avoid polluting other tests
        apps.app_configs.pop('djem_tests')
    
    def test_implicit_label__duplicate(self):
        """
        Test when called multiple times with no explicit app label provided.
        The second attempt should have no effect.
        """
        
        n = len(apps.app_configs)
        
        setup_test_app(self.package)
        self.assertEqual(len(apps.app_configs), n + 1)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')  # ensure all warnings are triggered
            
            setup_test_app(self.package)
            
            self.assertEqual(len(w), 1)
            self.assertTrue(w[0].message, 'Attempted setup of duplicate test app "djem_tests".')
            self.assertTrue(w[0].category, RuntimeWarning)
        
        self.assertEqual(len(apps.app_configs), n + 1)
        
        # Uninstall the app again to avoid polluting other tests
        apps.app_configs.pop('djem_tests')
