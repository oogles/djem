import pytz
import warnings

from django.apps import apps
from django.test import SimpleTestCase
from django.utils import timezone

from djem import UNDEFINED
from djem.utils.dt import TimeZoneHelper
from djem.utils.tests import setup_test_app


class UndefinedTestCase(SimpleTestCase):
    
    def test_falsey(self):
        
        self.assertFalse(UNDEFINED)
    
    def test_print(self):
        
        self.assertEqual(str(UNDEFINED), '<undefined>')


class TimeZoneHelperTestCase(SimpleTestCase):
    
    def test_init__good_string(self):
        """
        Test constructing a TimeZoneHelper object with a valid timezone string.
        """
        
        tz = 'Australia/Sydney'
        helper = TimeZoneHelper(tz)
        
        self.assertEqual(helper.tz.zone, tz)
    
    def test_init__bad_string(self):
        """
        Test constructing a TimeZoneHelper object with an invalid timezone string.
        """
        
        with self.assertRaises(pytz.UnknownTimeZoneError):
            TimeZoneHelper('fail')
    
    def test_init__UTC(self):
        """
        Test constructing a TimeZoneHelper object with the pytz UTC singleton.
        """
        
        tz = pytz.UTC
        helper = TimeZoneHelper(tz)
        
        self.assertIs(helper.tz, tz)
    
    def test_init__timezone(self):
        """
        Test constructing a TimeZoneHelper object with a valid pytz timezone
        instance.
        """
        
        tz = pytz.timezone('Australia/Sydney')
        helper = TimeZoneHelper(tz)
        
        self.assertIs(helper.tz, tz)
    
    def test_name(self):
        """
        Test the TimeZoneHelper ``name`` property for several different
        timezones.
        """
        
        self.assertEqual(TimeZoneHelper(pytz.UTC).name, 'UTC')
        self.assertEqual(TimeZoneHelper('Australia/Sydney').name, 'Australia/Sydney')
        self.assertEqual(TimeZoneHelper('US/Eastern').name, 'US/Eastern')
    
    def test_now__utc(self):
        """
        Test the TimeZoneHelper ``now`` method, using the UTC timezone.
        NOTE: This test is subject to some inaccuracy if run at the precise
        moment that caused the two compared datetimes to generate on either
        side of a minute interval.
        """
        
        fmt = '%Y-%m-%d %H:%M'
        
        # Generate the two "now" times as close together as possibly to minimise
        # the difference between them. Compare them with minute-resolution as
        # this is enough to detect timezone mismatches and the chance they will
        # generated either side of a minute interval is less than with seconds.
        now = timezone.now()
        helper_now = TimeZoneHelper(pytz.UTC).now()
        
        self.assertEqual(helper_now.strftime(fmt), now.strftime(fmt))
    
    def test_now__local(self):
        """
        Test the TimeZoneHelper ``now`` method, using a local timezone.
        NOTE: This test is subject to some inaccuracy if run at the precise
        moment that caused the two compared datetimes to generate on either
        side of a minute interval.
        """
        
        fmt = '%Y-%m-%d %H:%M'
        
        # Generate the two "now" times as close together as possibly to minimise
        # the difference between them. Compare them with minute-resolution as
        # this is enough to detect timezone mismatches and the chance they will
        # generated either side of a minute interval is less than with seconds.
        now = timezone.now()
        helper_now = TimeZoneHelper('Australia/Sydney').now()
        
        local = pytz.timezone('Australia/Sydney')
        local_now = local.normalize(now.astimezone(local))
        
        self.assertEqual(helper_now.strftime(fmt), local_now.strftime(fmt))
    
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
        helper_today = TimeZoneHelper(pytz.UTC).today()
        
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
        local = pytz.timezone('Australia/Sydney')
        local_today = local.normalize(now.astimezone(local)).date()
        
        helper_today = TimeZoneHelper('Australia/Sydney').today()
        
        self.assertEqual(helper_today, local_today)
    
    def test_stringify(self):
        """
        Test coercing TimeZoneHelper to a string.
        """
        
        self.assertEqual(str(TimeZoneHelper(pytz.UTC)), 'UTC')
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
