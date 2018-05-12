from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.views import View

from djem.auth import ObjectPermissionsBackend, PermissionRequiredMixin, permission_required

from .models import CustomUser, LogTest, OLPTest, UniversalOLPTest


def _test_view(request, obj=None):
    
    return HttpResponse('success')


class _TestView(PermissionRequiredMixin, View):
    
    def get(self, *args, **kwargs):
        
        return HttpResponse('success')


@override_settings(AUTH_USER_MODEL='tests.CustomUser')
class OLPMixinTestCase(TestCase):
    
    def setUp(self):
        
        self.user = CustomUser.objects.create_user('test.user')
    
    def test_clear_perm_cache__no_checks(self):
        """
        Test the clear_perm_cache() method before any permissions have been
        checked. It should have no effect.
        """
        
        user = self.user
        
        # OLPMixin defines the cache attribute by default, but it should be empty
        self.assertEqual(user._olp_cache, {})
        
        # Django's MLP cache attributes should not exist
        with self.assertRaises(AttributeError):
            getattr(user, '_user_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_group_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_perm_cache')
        
        # Clear the cache
        user.clear_perm_cache()
        
        self.assertEqual(user._olp_cache, {})
        
        with self.assertRaises(AttributeError):
            getattr(user, '_user_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_group_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_perm_cache')
    
    def test_clear_perm_cache__mlp(self):
        """
        Test the clear_perm_cache() method after model-level permissions have
        been checked. It should remove the attributes used by Django for
        various MLP caches.
        """
        
        user = self.user
        
        # Grant the user some permissions - both directly and via a group
        permissions = Permission.objects.filter(
            content_type__app_label='tests',
            content_type__model='olptest'
        )
        
        user.user_permissions.set(permissions.filter(codename__in=('add_olptest', 'change_olptest')))
        
        group = Group.objects.create(name='Test Group')
        group.permissions.set(permissions.filter(codename='open_olptest'))
        user.groups.add(group)
        
        # OLPMixin defines the cache attribute by default, but it should be empty
        self.assertEqual(user._olp_cache, {})
        
        # Django's MLP cache attributes should not exist
        with self.assertRaises(AttributeError):
            getattr(user, '_user_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_group_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_perm_cache')
        
        # Check a model-level permissions - the MLP caches only should populate
        user.has_perm('tests.open_olptest')
        
        self.assertEqual(user._olp_cache, {})
        self.assertEqual(len(user._user_perm_cache), 2)
        self.assertEqual(len(user._group_perm_cache), 1)
        self.assertEqual(len(user._perm_cache), 3)
        
        # Clear the cache - Django's MLP cache attributes should be removed
        user.clear_perm_cache()
        
        with self.assertRaises(AttributeError):
            getattr(user, '_user_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_group_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_perm_cache')
    
    def test_clear_perm_cache__olp(self):
        """
        Test the clear_perm_cache() method after object-level permissions have
        been checked. It should empty the dictionary used as the OLP cache, and
        remove the attributes used by Django for various MLP caches.
        """
        
        user = self.user
        
        # Grant the user some permissions - both directly and via a group
        permissions = Permission.objects.filter(
            content_type__app_label='tests',
            content_type__model='olptest'
        )
        
        user.user_permissions.set(permissions.filter(codename__in=('add_olptest', 'change_olptest')))
        
        group = Group.objects.create(name='Test Group')
        group.permissions.set(permissions.filter(codename='open_olptest'))
        user.groups.add(group)
        
        # OLPMixin defines the cache attribute by default, but it should be empty
        self.assertEqual(user._olp_cache, {})
        
        # Django's MLP cache attributes should not exist
        with self.assertRaises(AttributeError):
            getattr(user, '_user_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_group_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_perm_cache')
        
        # Check an object-level permission - the OLP and MLP caches should populate
        obj = OLPTest.objects.create()
        user.has_perm('tests.open_olptest', obj)
        
        self.assertEqual(len(user._olp_cache), 1)
        self.assertEqual(len(user._user_perm_cache), 2)
        self.assertEqual(len(user._group_perm_cache), 1)
        self.assertEqual(len(user._perm_cache), 3)
        
        # Clear the cache - the OLP cache dictionary should be emptied and the
        # Django's MLP cache attributes should be removed
        user.clear_perm_cache()
        
        self.assertEqual(user._olp_cache, {})
        
        with self.assertRaises(AttributeError):
            getattr(user, '_user_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_group_perm_cache')
        
        with self.assertRaises(AttributeError):
            getattr(user, '_perm_cache')
    
    def test_start_log(self):
        """
        Test the start_log() method. It should create an empty log entry, ready
        for adding to.
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        
        user.start_log('test_log')
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(user._active_logs['test_log'], [])
    
    def test_start_log__nested(self):
        """
        Test the start_log() method when an earlier log has already been started.
        It should create a second empty log entry, listed after the first.
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        
        # Start the first log
        user.start_log('test_log')
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(user._active_logs['test_log'], [])
        
        # Start a nested log
        user.start_log('nested_log')
        
        self.assertEqual(len(user._active_logs), 2)
        self.assertEqual(list(user._active_logs.keys()), ['test_log', 'nested_log'])
        self.assertEqual(user._active_logs['nested_log'], [])
    
    def test_start_log__repeat(self):
        """
        Test the start_log() method when attempting to start a nested log that
        uses the same name as an earlier, unfinished one. It should raise
        ValueError.
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        
        # Start the first log
        user.start_log('test_log')
        
        # Start a nested log
        user.start_log('nested_log')
        
        # Attempt starting a second nested log reusing an existing name
        with self.assertRaisesMessage(ValueError, 'A log named "test_log" is already active'):
            user.start_log('test_log')
    
    def test_end_log(self):
        """
        Test the end_log() method. It should move the log entry created by
        start_log() from the store of active logs to the store of finished ones.
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 0)
        
        user.start_log('test_log')
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(len(user._finished_logs), 0)
        
        user.end_log()
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 1)
        self.assertEqual(user._finished_logs['test_log'], [])
    
    def test_end_log__nested(self):
        """
        Test the end_log() method when ending a nested log. It should move the
        log entry the store of active logs to the store of finished ones,
        returning focus to the log that was active prior to the nested log
        being started.
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 0)
        
        # Start the first log
        user.start_log('test_log')
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(list(user._active_logs.keys()), ['test_log'])
        self.assertEqual(len(user._finished_logs), 0)
        
        # Start a nested log
        user.start_log('nested_log')
        
        self.assertEqual(len(user._active_logs), 2)
        self.assertEqual(list(user._active_logs.keys()), ['test_log', 'nested_log'])
        self.assertEqual(len(user._finished_logs), 0)
        
        # End the nested log
        user.end_log()
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(list(user._active_logs.keys()), ['test_log'])
        self.assertEqual(len(user._finished_logs), 1)
        self.assertEqual(list(user._finished_logs.keys()), ['nested_log'])
        
        # End the first log
        user.end_log()
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 2)
        self.assertEqual(list(user._finished_logs.keys()), ['nested_log', 'test_log'])
    
    def test_end_log__unstarted(self):
        """
        Test the end_log() method when no logs have been started. It should
        raise KeyError.
        """
        
        with self.assertRaisesMessage(KeyError, 'No active log to finish'):
            self.user.end_log()
    
    def test_discard_log(self):
        """
        Test the discard_log() method. It should remove the log entry created by
        start_log().
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 0)
        
        user.start_log('test_log')
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(len(user._finished_logs), 0)
        
        user.discard_log()
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 0)
    
    def test_discard_log__nested(self):
        """
        Test the discard_log() method on a nested log. It should remove the log
        entry created by start_log(), returning focus to the log that was
        active prior to the nested log being started.
        """
        
        user = self.user
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 0)
        
        # Start the first log
        user.start_log('test_log')
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(list(user._active_logs.keys()), ['test_log'])
        self.assertEqual(len(user._finished_logs), 0)
        
        # Start a nested log
        user.start_log('nested_log')
        
        self.assertEqual(len(user._active_logs), 2)
        self.assertEqual(list(user._active_logs.keys()), ['test_log', 'nested_log'])
        self.assertEqual(len(user._finished_logs), 0)
        
        # Discard the nested log
        user.discard_log()
        
        self.assertEqual(len(user._active_logs), 1)
        self.assertEqual(list(user._active_logs.keys()), ['test_log'])
        self.assertEqual(len(user._finished_logs), 0)
        
        # End the first log
        user.end_log()
        
        self.assertEqual(len(user._active_logs), 0)
        self.assertEqual(len(user._finished_logs), 1)
        self.assertEqual(list(user._finished_logs.keys()), ['test_log'])
    
    def test_discard_log__unstarted(self):
        """
        Test the discard_log() method when no logs have been started. It should
        raise KeyError.
        """
        
        with self.assertRaisesMessage(KeyError, 'No active log to discard'):
            self.user.discard_log()
    
    def test_log(self):
        """
        Test the log() method. It should append the given lines to the currently
        active log.
        """
        
        user = self.user
        
        user.start_log('test_log')
        self.assertEqual(user._active_logs['test_log'], [])
        
        user.log('first line', 'second line', 'third line')
        self.assertEqual(
            user._active_logs['test_log'],
            ['first line', 'second line', 'third line']
        )
        
        user.log('fourth line')
        self.assertEqual(
            user._active_logs['test_log'],
            ['first line', 'second line', 'third line', 'fourth line']
        )
    
    def test_log__nested(self):
        """
        Test the log() method when a nested log has been started. It should
        append the given lines to the currently active log.
        """
        
        user = self.user
        
        user.start_log('test_log')
        user.log('first line 1', 'second line 1', 'third line 1')
        self.assertEqual(
            user._active_logs['test_log'],
            ['first line 1', 'second line 1', 'third line 1']
        )
        
        user.start_log('nested_log')
        user.log('first line 2', 'second line 2', 'third line 2')
        self.assertEqual(
            user._active_logs['test_log'],
            ['first line 1', 'second line 1', 'third line 1']
        )
        self.assertEqual(
            user._active_logs['nested_log'],
            ['first line 2', 'second line 2', 'third line 2']
        )
        
        user.log('fourth line 2')
        self.assertEqual(
            user._active_logs['test_log'],
            ['first line 1', 'second line 1', 'third line 1']
        )
        self.assertEqual(
            user._active_logs['nested_log'],
            ['first line 2', 'second line 2', 'third line 2', 'fourth line 2']
        )
        
        user.end_log()
        
        user.log('fourth line 1')
        self.assertEqual(
            user._active_logs['test_log'],
            ['first line 1', 'second line 1', 'third line 1', 'fourth line 1']
        )
        self.assertEqual(
            user._finished_logs['nested_log'],
            ['first line 2', 'second line 2', 'third line 2', 'fourth line 2']
        )
    
    def test_log__unstarted(self):
        """
        Test the log() method when no logs have been started. It should raise
        KeyError.
        """
        
        with self.assertRaises(KeyError):
            self.user.log('first line', 'second line')
    
    def test_get_log(self):
        """
        Test the get_log() method. It should return the log entry for the named
        log.
        """
        
        user = self.user
        
        user.start_log('test_log')
        user.log('first line', 'second line')
        user.end_log()
        
        log = user.get_log('test_log')
        self.assertEqual(log, 'first line\nsecond line')
        
        raw_log = user.get_log('test_log', raw=True)
        self.assertEqual(raw_log, ['first line', 'second line'])
    
    def test_get_log__unstarted(self):
        """
        Test the get_log() method when no log by the given name has been started.
        It should raise KeyError.
        """
        
        with self.assertRaisesMessage(KeyError, 'No log found for "test_log". Has it been finished?'):
            self.user.get_log('test_log')
    
    def test_get_log__unfinished(self):
        """
        Test the get_log() method when a log by the given name has been started,
        but not finished. It should raise KeyError.
        """
        
        user = self.user
        
        user.start_log('test_log')
        
        with self.assertRaisesMessage(KeyError, 'No log found for "test_log". Has it been finished?'):
            user.get_log('test_log')
    
    def test_get_last_log(self):
        """
        Test the get_last_log() method. It should return the log entry for most
        recently finished log.
        """
        
        user = self.user
        
        user.start_log('log-1')
        user.log('log 1')
        user.end_log()
        
        self.assertEqual(user.get_last_log(), 'log 1')
        self.assertEqual(user.get_last_log(raw=True), ['log 1'])
        
        user.start_log('log-2')
        user.log('log 2')
        user.end_log()
        
        user.start_log('log-3')
        user.log('log 3')
        user.end_log()
        
        self.assertEqual(user.get_last_log(), 'log 3')
        self.assertEqual(user.get_last_log(raw=True), ['log 3'])
        
        # Ensure all three logs are still there to retrieve again later if
        # necessary
        self.assertEqual(len(user._finished_logs), 3)
        
        self.assertEqual(user.get_log('log-2'), 'log 2')
    
    def test_get_last_log__none_finished(self):
        """
        Test the get_last_log() method when no logs have been finished. It
        should raise KeyError.
        """
        
        with self.assertRaisesMessage(KeyError, 'No finished logs to retrieve'):
            self.user.get_last_log()
    
    def test_repeating_logs(self):
        """
        Test the log() method with multiple nested logs, including reusing
        previous log names for logs that have been properly ended (as might
        occur during a loop). It should append the given lines to the currently
        active log.
        """
        
        user = self.user
        
        user.start_log('test_log')
        user.log('first line', 'second line', 'third line')
        
        user.start_log('nested_log')
        user.log('first run')
        user.end_log()
        
        self.assertEqual(user.get_last_log(), 'first run')
        
        # Ensure a random log that occurs between two runs of the same log does
        # not keep the second run from being "last". i.e. when a log with the
        # same name as an earlier log is run, it should always append to the
        # end of the OrderedDict of finished logs, not update the existing entry,
        # which is potentially further back in the "list".
        user.start_log('random_log')
        user.log('second run')
        user.end_log()
        
        user.log('fourth line')
        
        user.start_log('nested_log')
        user.log('second run')
        user.end_log()
        
        self.assertEqual(user.get_last_log(), 'second run')
        
        user.log('fifth line')
        
        user.start_log('nested_log')
        user.log('third run')
        user.end_log()
        
        self.assertEqual(user.get_last_log(), 'third run')
        
        user.end_log()
        
        self.assertEqual(
            user.get_log('test_log', raw=True),
            ['first line', 'second line', 'third line', 'fourth line', 'fifth line']
        )
        
        self.assertEqual(user.get_log('nested_log'), 'third run')
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=0)
    def test_has_perm__logging__0(self):
        """
        Test the overridden has_perm() method when the DJEM_PERM_LOG_VERBOSITY
        setting is 0 (no logging). No log should be created automatically.
        """
        
        user = self.user
        
        user.has_perm('tests.mlp_logtest')
        
        with self.assertRaisesMessage(KeyError, 'No finished logs to retrieve'):
            user.get_last_log()
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=1)
    def test_has_perm__logging__1__mlp(self):
        """
        Test the overridden has_perm() method for a model-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 1 (automatic logging, minimal output).
        A log should be created automatically with a minimum of automatic log
        entries.
        """
        
        user = self.user
        
        user.has_perm('tests.mlp_logtest')
        
        # Only one log - thet for the model-level check - should be created
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            '\nRESULT: Permission Denied'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=1)
    def test_has_perm__logging__1__olp(self):
        """
        Test the overridden has_perm() method for an object-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 1 (automatic logging, minimal output).
        A log should be created automatically with a minimum of automatic log
        entries.
        """
        
        user = self.user
        
        # Grant the user the model-level permission so that object-level checks
        # are performed
        user.user_permissions.add(Permission.objects.get(codename='olp_logtest'))
        
        obj = LogTest.objects.create()
        
        user.has_perm('tests.olp_logtest', obj)
        
        # Two logs should be created - one for the model-level permission
        # check and another for the object-level permission check
        self.assertEqual(len(user._finished_logs), 2)
        self.assertEqual(
            list(user._finished_logs.keys()),
            ['auto-tests.olp_logtest', 'auto-tests.olp_logtest-{0}'.format(obj.pk)]
        )
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Model-level Result: Granted\n',
            'This permission is restricted.',
            '\nRESULT: Permission Denied'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=1)
    def test_has_perm__logging__1__mlp__superuser(self):
        """
        Test the overridden has_perm() method for a model-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 1 (automatic logging, minimal output)
        and when the user is a superuser. A log should be created automatically
        with a minimum of automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        user.has_perm('tests.mlp_logtest')
        
        # Only one log - thet for the model-level check - should be created
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Active superuser: Implicit permission',
            '\nRESULT: Permission Granted'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=1)
    def test_has_perm__logging__1__olp__superuser(self):
        """
        Test the overridden has_perm() method for an object-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 1 (automatic logging, minimal output)
        and when the user is a superuser. A log should be created automatically
        with a minimum of automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        obj = LogTest.objects.create()
        
        user.has_perm('tests.olp_logtest', obj)
        
        # Only one log should be created - the object-level permission should
        # be implicitly granted without even needing the model-level check first
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Active superuser: Implicit permission',
            '\nRESULT: Permission Granted'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=1, DJEM_UNIVERSAL_OLP=True)
    def test_has_perm__logging__1__mlp__superuser__universal_olp(self):
        """
        Test the overridden has_perm() method for a model-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 1 (automatic logging, minimal output),
        DJEM_UNIVERSAL_OLP is True, and when the user is a superuser. A log
        should be created automatically with a minimum of automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        user.has_perm('tests.mlp_logtest')
        
        # Only one log - thet for the model-level check - should be created
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Active superuser: Implicit permission (model-level)',
            '\nRESULT: Permission Granted'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=1, DJEM_UNIVERSAL_OLP=True)
    def test_has_perm__logging__1__olp__superuser__universal_olp(self):
        """
        Test the overridden has_perm() method for an object-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 1 (automatic logging, minimal output),
        DJEM_UNIVERSAL_OLP is True, and when the user is a superuser. A log
        should be created automatically with a minimum of automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        obj = LogTest.objects.create()
        
        user.has_perm('tests.olp_logtest', obj)
        
        # Two logs should be created - one for the model-level permission
        # check and another for the object-level permission check (which is
        # still performed for superusers with universal OLP)
        self.assertEqual(len(user._finished_logs), 2)
        self.assertEqual(
            list(user._finished_logs.keys()),
            ['auto-tests.olp_logtest', 'auto-tests.olp_logtest-{0}'.format(obj.pk)]
        )
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Active superuser: Implicit permission (model-level)',
            'Model-level Result: Granted\n',
            'This permission is restricted.',
            '\nRESULT: Permission Denied'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=2)
    def test_has_perm__logging__2__mlp(self):
        """
        Test the overridden has_perm() method for a model-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 2 (automatic logging, standard output).
        A log should be created automatically with all standard automatic log
        entries.
        """
        
        user = self.user
        
        user.has_perm('tests.mlp_logtest')
        
        # Only one log - thet for the model-level check - should be created
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Permission: tests.mlp_logtest',
            'User: test.user ({})\n'.format(self.user.pk),
            '\nRESULT: Permission Denied'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=2)
    def test_has_perm__logging__2__olp(self):
        """
        Test the overridden has_perm() method for an object-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 2 (automatic logging, standard output).
        A log should be created automatically with all standard automatic log
        entries.
        """
        
        user = self.user
        
        # Grant the user the model-level permission so that object-level checks
        # are performed
        user.user_permissions.add(Permission.objects.get(codename='olp_logtest'))
        
        obj = LogTest.objects.create()
        
        user.has_perm('tests.olp_logtest', obj)
        
        # Two logs should be created - one for the model-level permission
        # check and another for the object-level permission check
        self.assertEqual(len(user._finished_logs), 2)
        self.assertEqual(
            list(user._finished_logs.keys()),
            ['auto-tests.olp_logtest', 'auto-tests.olp_logtest-{0}'.format(obj.pk)]
        )
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Permission: tests.olp_logtest',
            'User: test.user ({})'.format(self.user.pk),
            'Object: Log Test #{0} ({0})\n'.format(obj.pk),
            'Model-level Result: Granted\n',
            'This permission is restricted.',
            '\nRESULT: Permission Denied'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=2)
    def test_has_perm__logging__2__mlp__superuser(self):
        """
        Test the overridden has_perm() method for a model-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 2 (automatic logging, standard output)
        and when the user is a superuser. A log should be created automatically
        with all standard automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        user.has_perm('tests.mlp_logtest')
        
        # Only one log - thet for the model-level check - should be created
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Permission: tests.mlp_logtest',
            'User: test.user ({})\n'.format(self.user.pk),
            'Active superuser: Implicit permission',
            '\nRESULT: Permission Granted'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=2)
    def test_has_perm__logging__2__olp__superuser(self):
        """
        Test the overridden has_perm() method for an object-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 2 (automatic logging, standard output)
        and when the user is a superuser. A log should be created automatically
        with all standard automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        obj = LogTest.objects.create()
        
        user.has_perm('tests.olp_logtest', obj)
        
        # Only one log should be created - the object-level permission should
        # be implicitly granted without even needing the model-level check first
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Permission: tests.olp_logtest',
            'User: test.user ({})'.format(self.user.pk),
            'Object: Log Test #{0} ({0})\n'.format(obj.pk),
            'Active superuser: Implicit permission',
            '\nRESULT: Permission Granted'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=2, DJEM_UNIVERSAL_OLP=True)
    def test_has_perm__logging__2__mlp__superuser__universal_olp(self):
        """
        Test the overridden has_perm() method for a model-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 2 (automatic logging, standard output),
        DJEM_UNIVERSAL_OLP is True, and when the user is a superuser. A log
        should be created automatically with all standard automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        user.has_perm('tests.mlp_logtest')
        
        # Only one log - thet for the model-level check - should be created
        self.assertEqual(len(user._finished_logs), 1)
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Permission: tests.mlp_logtest',
            'User: test.user ({})\n'.format(self.user.pk),
            'Active superuser: Implicit permission (model-level)',
            '\nRESULT: Permission Granted'
        ])
    
    @override_settings(DJEM_PERM_LOG_VERBOSITY=2, DJEM_UNIVERSAL_OLP=True)
    def test_has_perm__logging__2__olp__superuser__universal_olp(self):
        """
        Test the overridden has_perm() method for an object-level check when the
        DJEM_PERM_LOG_VERBOSITY setting is 2 (automatic logging, standard output),
        DJEM_UNIVERSAL_OLP is True, and when the user is a superuser. A log
        should be created automatically with all standard automatic log entries.
        """
        
        user = self.user
        user.is_superuser = True
        user.save()
        
        obj = LogTest.objects.create()
        
        user.has_perm('tests.olp_logtest', obj)
        
        # Two logs should be created - one for the model-level permission
        # check and another for the object-level permission check (which is
        # still performed for superusers with universal OLP)
        self.assertEqual(len(user._finished_logs), 2)
        self.assertEqual(
            list(user._finished_logs.keys()),
            ['auto-tests.olp_logtest', 'auto-tests.olp_logtest-{0}'.format(obj.pk)]
        )
        
        log = user.get_last_log(raw=True)
        self.assertEqual(log, [
            'Permission: tests.olp_logtest',
            'User: test.user ({})'.format(self.user.pk),
            'Object: Log Test #{0} ({0})\n'.format(obj.pk),
            'Active superuser: Implicit permission (model-level)',
            'Model-level Result: Granted\n',
            'This permission is restricted.',
            '\nRESULT: Permission Denied'
        ])


@override_settings(AUTH_USER_MODEL='auth.User')
class OLPTestCase(TestCase):
    
    UserModel = User
    TestModel = OLPTest
    model_name = 'olptest'
    
    def setUp(self):
        
        group1 = Group.objects.create(name='Test Group 1')
        group2 = Group.objects.create(name='Test Group 2')
        
        user1 = self.UserModel.objects.create_user('test1')
        user1.groups.add(group1)
        
        user2 = self.UserModel.objects.create_user('test2')
        user2.groups.add(group2)
        
        # Grant both users and both groups all permissions for OLPTest, at
        # the model level (except "closed", only accessible to super users)
        permissions = Permission.objects.filter(
            content_type__app_label='tests',
            content_type__model=self.model_name
        ).exclude(codename='closed_{0}'.format(self.model_name))
        
        user1.user_permissions.set(permissions)
        user2.user_permissions.set(permissions)
        group1.permissions.set(permissions)
        group2.permissions.set(permissions)
        
        self.user1 = user1
        self.user2 = user2
        self.group1 = group1
        self.group2 = group2
        self.all_permissions = permissions
    
    def perm(self, perm_name):
        
        return 'tests.{0}_{1}'.format(perm_name, self.model_name)
    
    def cache(self, cache_type, perm_name, obj):
        
        return '{0}-tests.{1}_{2}-{3}'.format(
            cache_type,
            perm_name,
            self.model_name,
            obj.pk
        )
    
    def cache_empty_test(self, user):
        
        # The cache attribute on the user does not exist by default
        with self.assertRaises(AttributeError):
            getattr(user, '_olp_cache')
    
    def cache_reset_test(self, user):
        
        # Requerying for the user is the only way to reset the cache
        user = self.UserModel.objects.get(pk=user.pk)
        
        self.cache_empty_test(user)
    
    def test_auth__valid(self):
        """
        Test the backend does not interfere with valid user authentication.
        """
        
        user = self.user1
        user.set_password('blahblahblah')
        user.save()
        
        self.assertTrue(authenticate(username='test1', password='blahblahblah'))
    
    def test_auth__invalid(self):
        """
        Test the backend does not interfere with invalid user authentication.
        """
        
        self.assertFalse(authenticate(username='test1', password='badpassword'))
    
    def test_has_perm__no_model_level(self):
        """
        Test a user is denied object-level permissions if they don't have the
        corresponding model-level permissions.
        """
        
        obj = self.TestModel.objects.create()
        
        user1 = self.UserModel.objects.create_user('useless')
        perm1 = user1.has_perm(self.perm('open'), obj)
        self.assertFalse(perm1)
        
        user2 = self.UserModel.objects.create_user('useful')
        user2.user_permissions.add(Permission.objects.get(codename='open_{0}'.format(self.model_name)))
        perm2 = user2.has_perm(self.perm('open'), obj)
        self.assertTrue(perm2)
    
    def test_has_perm__inactive_user(self):
        """
        Test an inactive user is denied object-level permissions without ever
        reaching the object's permission access method.
        """
        
        user = self.UserModel.objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Grant the user the "open" permission to ensure it is their
        # inactive-ness that denies them permission
        user.user_permissions.add(Permission.objects.get(codename='open_{0}'.format(self.model_name)))
        
        obj = self.TestModel.objects.create()
        
        perm = user.has_perm(self.perm('open'), obj)
        
        self.assertFalse(perm)
    
    def test_has_perm__super_user(self):
        """
        Test a superuser is granted object-level permissions without ever
        reaching the object's permission access method.
        """
        
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # Deliberately do not grant the user the "open" permission to
        # ensure it is their super-ness that grants them permission
        
        obj = self.TestModel.objects.create()
        
        perm = user.has_perm(self.perm('open'), obj)
        
        self.assertTrue(perm)
    
    def test_has_perm__inactive_super_user(self):
        """
        Test an inactive superuser is denied object-level permissions without
        ever reaching the object's permission access method, despite being a
        superuser.
        """
        
        user = self.UserModel.objects.create_user('superinactive')
        user.is_superuser = True
        user.is_active = False
        user.save()
        
        # Grant the user the "open" permission to ensure it is their
        # inactive-ness that denies them permission
        user.user_permissions.add(Permission.objects.get(codename='open_{0}'.format(self.model_name)))
        
        obj = self.TestModel.objects.create()
        
        perm = user.has_perm(self.perm('open'), obj)
        
        self.assertFalse(perm)
    
    def test_has_perm__no_access_fn(self):
        """
        Test that the lack of defined permission access methods on the object
        being tested does not deny access (checking a permission without passing
        an object should be identical to checking a permission with passing an
        object, if there is no object-level logic involved in granting/denying
        the permission).
        """
        
        obj = self.TestModel.objects.create()
        
        # Test without object
        model_perm = self.user1.has_perm(self.perm('add'))
        self.assertTrue(model_perm)
        
        # Test with object
        obj_perm = self.user1.has_perm(self.perm('add'), obj)
        self.assertTrue(obj_perm)
    
    def test_has_perm__user_only_logic(self):
        """
        Test that an object's user-based permission access method can be used
        to grant permissions to some users and not others, when all users have
        the same permission at the model level, by returning True/False, and
        that the result is unaffected by having no group-based logic defined.
        """
        
        obj = self.TestModel.objects.create(user=self.user1)
        
        perm1 = self.user1.has_perm(self.perm('user_only'), obj)
        perm2 = self.user2.has_perm(self.perm('user_only'), obj)
        
        self.assertTrue(perm1)
        self.assertFalse(perm2)
    
    def test_has_perm__group_only_logic(self):
        """
        Test that an object's group-based permission access method can be used
        to grant permissions to some users and not others based on their
        groups, when all groups have the same permission at the model level, and
        that the result is unaffected by having no user-based logic defined.
        """
        
        obj = self.TestModel.objects.create(group=self.group1)
        
        perm1 = self.user1.has_perm(self.perm('group_only'), obj)
        perm2 = self.user2.has_perm(self.perm('group_only'), obj)
        
        self.assertTrue(perm1)
        self.assertFalse(perm2)
    
    def test_has_perm__combined_logic(self):
        """
        Test that an object's user-based AND group-based permission access
        methods can be used together to grant permissions to some users and not
        others, with either one able to grant the permission if the other does
        not.
        """
        
        obj1 = self.TestModel.objects.create(user=self.user1, group=self.group2)
        obj2 = self.TestModel.objects.create()
        
        # User = True, Group untested
        user_perm1 = self.user1.has_perm(self.perm('user_only'), obj1)
        group_perm1 = self.user1.has_perm(self.perm('group_only'), obj1)
        combined_perm1 = self.user1.has_perm(self.perm('combined'), obj1)
        self.assertTrue(user_perm1)
        self.assertFalse(group_perm1)
        self.assertTrue(combined_perm1)
        
        # User = False, Group = True
        user_perm2 = self.user2.has_perm(self.perm('user_only'), obj1)
        group_perm2 = self.user2.has_perm(self.perm('group_only'), obj1)
        combined_perm2 = self.user2.has_perm(self.perm('combined'), obj1)
        self.assertFalse(user_perm2)
        self.assertTrue(group_perm2)
        self.assertTrue(combined_perm2)
        
        # User = False, Group = False
        user_perm3 = self.user1.has_perm(self.perm('user_only'), obj2)
        group_perm3 = self.user1.has_perm(self.perm('group_only'), obj2)
        combined_perm3 = self.user1.has_perm(self.perm('combined'), obj2)
        self.assertFalse(user_perm3)
        self.assertFalse(group_perm3)
        self.assertFalse(combined_perm3)
    
    def test_has_perm__permissiondenied(self):
        """
        Test that an object's permission access methods can raise the
        PermissionDenied exception and have it treated as returning False.
        """
        
        obj = self.TestModel.objects.create(user=self.user1)
        
        perm = self.user1.has_perm(self.perm('deny'), obj)
        
        self.assertFalse(perm)
    
    def test_has_perm__cache(self):
        """
        Test that determining a user's object-level permission creates a cache
        on the User instance of the result, for the permission and object tested.
        """
        
        user = self.user1
        obj = self.TestModel.objects.create()
        user_perm_cache_name = self.cache('user', 'combined', obj)
        group_perm_cache_name = self.cache('group', 'combined', obj)
        
        # Test cache does not exist
        self.cache_empty_test(user)
        
        user.has_perm(self.perm('combined'), obj)
        
        # Test cache has been set
        self.assertFalse(user._olp_cache[user_perm_cache_name])
        self.assertFalse(user._olp_cache[group_perm_cache_name])
        
        # Test resetting the cache
        self.cache_reset_test(user)
    
    def test_has_perms(self):
        """
        Test PermissionsMixin.has_perms works and correctly identifies the
        object-level permissions the user has.
        """
        
        obj = self.TestModel.objects.create(user=self.user1)
        
        perm1 = self.user1.has_perms((self.perm('open'), self.perm('combined')), obj)
        self.assertTrue(perm1)
        
        perm2 = self.user2.has_perms((self.perm('open'), self.perm('combined')), obj)
        self.assertFalse(perm2)
    
    def test_get_user_permissions(self):
        """
        Test ObjectPermissionsBackend.get_user_permissions() works and correctly
        identifies the object-level permissions the user has.
        Test the backend directly, without going through User/PermissionsMixin
        as they don't provide a mapping through to it.
        """
        
        backend = ObjectPermissionsBackend()
        obj = self.TestModel.objects.create(user=self.user1, group=self.group1)
        
        self.assertEqual(backend.get_user_permissions(self.user1, obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('user_only'),
            self.perm('combined')
        })
        
        self.assertEqual(backend.get_user_permissions(self.user2, obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open')
        })
    
    def test_get_user_permissions__inactive_user(self):
        """
        Test ObjectPermissionsBackend.get_user_permissions() correctly denies
        all permissions to inactive users.
        Test the backend directly, without going through User/PermissionsMixin
        as they don't provide a mapping through to it.
        """
        
        backend = ObjectPermissionsBackend()
        user = self.UserModel.objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = self.TestModel.objects.create()
        
        perms = backend.get_user_permissions(user, obj)
        self.assertEqual(perms, set())
    
    def test_get_user_permissions__super_user(self):
        """
        Test ObjectPermissionsBackend.get_user_permissions() correctly grants
        all permissions to superusers.
        Test the backend directly, without going through User/PermissionsMixin
        as they don't provide a mapping through to it.
        """
        
        backend = ObjectPermissionsBackend()
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them permission
        
        obj = self.TestModel.objects.create()
        
        perms = backend.get_user_permissions(user, obj)
        self.assertEqual(perms, {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('closed'),
            self.perm('user_only'),
            self.perm('group_only'),
            self.perm('combined'),
            self.perm('deny')
        })
    
    def test_get_user_permissions__inactive_super_user(self):
        """
        Test ObjectPermissionsBackend.get_user_permissions() correctly denies
        all permissions to inactive users, even superusers.
        Test the backend directly, without going through User/PermissionsMixin
        as they don't provide a mapping through to it.
        """
        
        backend = ObjectPermissionsBackend()
        user = self.UserModel.objects.create_user('superinactive')
        user.is_superuser = True
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = self.TestModel.objects.create()
        
        perms = backend.get_user_permissions(user, obj)
        self.assertEqual(perms, set())
    
    def test_get_user_permissions__cache(self):
        """
        Test that PermissionsMixin.get_user_permissions correctly creates a
        a cache on the User instance of the result of each permission test, for
        the permission and object tested.
        """
        
        backend = ObjectPermissionsBackend()
        user = self.user1
        obj = self.TestModel.objects.create()
        
        expected_caches = (
            self.cache('user', 'add', obj),
            self.cache('user', 'change', obj),
            self.cache('user', 'delete', obj),
            self.cache('user', 'open', obj),
            self.cache('user', 'user_only', obj),
            self.cache('user', 'group_only', obj),
            self.cache('user', 'combined', obj),
            self.cache('user', 'deny', obj)
        )
        
        unexpected_caches = (
            self.cache('user', 'closed', obj),  # does not reach OLP stage (MLP denied)
        )
        
        unexpected_caches = [s.format(obj.pk) for s in unexpected_caches]
        
        # Test cache does not exist
        self.cache_empty_test(user)
        
        backend.get_user_permissions(user, obj)
        
        # Test expected caches have been set
        for cache_key in expected_caches:
            try:
                user._olp_cache[cache_key]
            except (AttributeError, KeyError):  # pragma: no cover
                self.fail('Cache not set: {0}'.format(cache_key))
        
        # Test unexpected caches still do not exist
        for cache_key in unexpected_caches:
            with self.assertRaises(KeyError):
                user._olp_cache[cache_key]
        
        # Test resetting the cache
        self.cache_reset_test(user)
    
    def test_get_group_permissions(self):
        """
        Test PermissionsMixin.get_group_permissions() works and correctly
        identifies the object-level permissions the user has.
        """
        
        obj = self.TestModel.objects.create(user=self.user1, group=self.group1)
        
        self.assertEqual(self.user1.get_group_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('group_only'),
            self.perm('combined'),
            self.perm('deny')  # no group-based access method, defaults open
        })
        
        self.assertEqual(self.user2.get_group_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('deny')  # no group-based access method, defaults open
        })
    
    def test_get_group_permissions__inactive_user(self):
        """
        Test PermissionsMixin.get_group_permissions() correctly denies all
        permissions to inactive users.
        """
        
        user = self.UserModel.objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = self.TestModel.objects.create(user=user)
        
        perms = user.get_group_permissions(obj)
        self.assertEqual(perms, set())
    
    def test_get_group_permissions__super_user(self):
        """
        Test PermissionsMixin.get_group_permissions() correctly grants all
        permissions to superusers.
        """
        
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them permission
        
        obj = self.TestModel.objects.create()
        
        self.assertEqual(user.get_all_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('closed'),
            self.perm('user_only'),
            self.perm('group_only'),
            self.perm('combined'),
            self.perm('deny')
        })
    
    def test_get_group_permissions__inactive_super_user(self):
        """
        Test PermissionsMixin.get_group_permissions() correctly denies all
        permissions to inactive users, even superusers.
        """
        
        user = self.UserModel.objects.create_user('superinactive')
        user.is_superuser = True
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = self.TestModel.objects.create(user=user)
        
        perms = user.get_group_permissions(obj)
        self.assertEqual(perms, set())
    
    def test_get_group_permissions__cache(self):
        """
        Test that PermissionsMixin.get_group_permissions() correctly creates a
        a cache on the User instance of the result of each permission test, for
        the permission and object tested.
        """
        
        user = self.user1
        obj = self.TestModel.objects.create()
        
        expected_caches = (
            self.cache('group', 'add', obj),
            self.cache('group', 'change', obj),
            self.cache('group', 'delete', obj),
            self.cache('group', 'open', obj),
            self.cache('group', 'user_only', obj),
            self.cache('group', 'group_only', obj),
            self.cache('group', 'combined', obj),
            self.cache('group', 'deny', obj)
        )
        
        unexpected_caches = (
            self.cache('group', 'closed', obj),  # does not reach OLP stage (MLP denied)
        )
        
        unexpected_caches = [s.format(obj.pk) for s in unexpected_caches]
        
        # Test cache does not exist
        self.cache_empty_test(user)
        
        user.get_group_permissions(obj)
        
        # Test expected caches have been set
        for cache_key in expected_caches:
            try:
                user._olp_cache[cache_key]
            except (AttributeError, KeyError):  # pragma: no cover
                self.fail('Cache not set: {0}'.format(cache_key))
        
        # Test unexpected caches still do not exist
        for cache_key in unexpected_caches:
            with self.assertRaises(KeyError):
                user._olp_cache[cache_key]
        
        # Test resetting the cache
        self.cache_reset_test(user)
    
    def test_get_all_permissions(self):
        """
        Test PermissionsMixin.get_all_permissions() works and correctly
        identifies the object-level permissions the user has.
        """
        
        obj = self.TestModel.objects.create(user=self.user1, group=self.group1)
        
        self.assertEqual(self.user1.get_all_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('user_only'),
            self.perm('group_only'),
            self.perm('combined')
        })
        
        self.assertEqual(self.user2.get_all_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open')
        })
    
    def test_get_all_permissions__inactive_user(self):
        """
        Test PermissionsMixin.get_all_permissions() correctly denies all
        permissions to inactive users.
        """
        
        user = self.UserModel.objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = self.TestModel.objects.create(user=user)
        
        perms = user.get_all_permissions(obj)
        self.assertEqual(perms, set())
    
    def test_get_all_permissions__super_user(self):
        """
        Test PermissionsMixin.get_all_permissions() correctly grants all
        permissions to superusers.
        """
        
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them permission
        
        obj = self.TestModel.objects.create()
        
        self.assertEqual(user.get_all_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('closed'),
            self.perm('user_only'),
            self.perm('group_only'),
            self.perm('combined'),
            self.perm('deny')
        })
    
    def test_get_all_permissions__inactive_super_user(self):
        """
        Test PermissionsMixin.get_all_permissions() correctly denies all
        permissions to inactive users, even superusers.
        """
        
        user = self.UserModel.objects.create_user('superinactive')
        user.is_superuser = True
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = self.TestModel.objects.create(user=user)
        
        perms = user.get_all_permissions(obj)
        self.assertEqual(perms, set())
    
    def test_get_all_permissions__cache(self):
        """
        Test that PermissionsMixin.get_all_permissions() correctly creates a
        a cache on the User instance of the result of each permission test, for
        the permission and object tested.
        """
        
        user = self.user1
        obj = self.TestModel.objects.create(user=user)
        
        expected_caches = (
            self.cache('user', 'add', obj),
            self.cache('group', 'add', obj),
            
            self.cache('user', 'change', obj),
            self.cache('group', 'change', obj),
            
            self.cache('user', 'delete', obj),
            self.cache('group', 'delete', obj),
            
            self.cache('user', 'open', obj),  # group won't need checking
            
            self.cache('user', 'user_only', obj),  # group won't need checking
            
            self.cache('user', 'group_only', obj),
            self.cache('group', 'group_only', obj),
            
            self.cache('user', 'combined', obj),  # group won't need checking
            
            self.cache('user', 'deny', obj),
            self.cache('group', 'deny', obj)
        )
        
        expected_caches = [s.format(obj.pk) for s in expected_caches]
        
        unexpected_caches = (
            # Does not reach OLP stage (MLP denied)
            self.cache('user', 'closed', obj),
            self.cache('group', 'closed', obj),
            
            #  Does not reach group OLP stage (user OLP granted)
            self.cache('group', 'open', obj),
            self.cache('group', 'user_only', obj),
            self.cache('group', 'combined', obj)
        )
        
        unexpected_caches = [s.format(obj.pk) for s in unexpected_caches]
        
        # Test cache does not exist
        self.cache_empty_test(user)
        
        user.get_all_permissions(obj)
        
        # Test expected caches have been set
        for cache_key in expected_caches:
            try:
                user._olp_cache[cache_key]
            except (AttributeError, KeyError):  # pragma: no cover
                self.fail('Cache not set: {0}'.format(cache_key))
        
        # Test unexpected caches still do not exist
        for cache_key in unexpected_caches:
            with self.assertRaises(KeyError):
                user._olp_cache[cache_key]
        
        # Test resetting the cache
        self.cache_reset_test(user)


class OLPCacheMixin:
    
    #
    # Overrides for the cache testing helper methods defined on OLPTestCase,
    # for test cases that use a user model that incorporates OLPMixin
    #
    
    def cache_empty_test(self, user):
        
        # OLPMixin defines the cache attribute by default, but it should be empty
        self.assertEqual(user._olp_cache, {})
    
    def cache_reset_test(self, user):

        # OLPMixin provides a method to clear the cache
        user.clear_perm_cache()

        self.cache_empty_test(user)


@override_settings(AUTH_USER_MODEL='tests.CustomUser', DJEM_UNIVERSAL_OLP=False)
class UniversalOLPFalseTestCase(OLPCacheMixin, OLPTestCase):
    
    #
    # A repeat of the object-level permissions tests for the default user model,
    # but for one incorporating OLPMixin, and with DJEM_UNIVERSAL_OLP=False.
    # Results should be identical.
    #
    
    UserModel = CustomUser
    TestModel = UniversalOLPTest
    model_name = 'universalolptest'
    

@override_settings(AUTH_USER_MODEL='tests.CustomUser', DJEM_UNIVERSAL_OLP=True)
class UniversalOLPTrueTestCase(OLPCacheMixin, OLPTestCase):
    
    #
    # A repeat of the object-level permissions tests for the default user model,
    # but for one incorporating OLPMixin, and with DJEM_UNIVERSAL_OLP=True.
    # Results should be identical EXCEPT for the tests involving active
    # superusers, which should actually perform object-level permissions rather
    # than unconditionally granting such users every permission.
    #
    
    UserModel = CustomUser
    TestModel = UniversalOLPTest
    model_name = 'universalolptest'
    
    def test_get_user_permissions__super_user(self):
        """
        Test ObjectPermissionsBackend.get_user_permissions() correctly subjects
        superusers to the same object-level permission logic as a standard user
        (they simply don't require the model-level permission be granted to
        them explicitly).
        Test the backend directly, without going through User/PermissionsMixin
        as they don't provide a mapping through to it.
        """
        
        backend = ObjectPermissionsBackend()
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them model-level permission
        
        obj = self.TestModel.objects.create()
        
        perms = backend.get_user_permissions(user, obj)
        self.assertEqual(perms, {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('closed')
        })
    
    def test_get_group_permissions__super_user(self):
        """
        Test PermissionsMixin.get_group_permissions() correctly subjects
        superusers to the same object-level permission logic as a standard user
        (they simply don't require the model-level permission be granted to
        them explicitly).
        """
        
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them model-level permission
        
        obj = self.TestModel.objects.create()
        
        self.assertEqual(user.get_all_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('closed')
        })
    
    def test_get_all_permissions__super_user(self):
        """
        Test PermissionsMixin.get_all_permissions() correctly subjects
        superusers to the same object-level permission logic as a standard user
        (they simply don't require the model-level permission be granted to
        them explicitly).
        """
        
        user = self.UserModel.objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them model-level permission
        
        obj = self.TestModel.objects.create()
        
        self.assertEqual(user.get_all_permissions(obj), {
            self.perm('delete'),
            self.perm('change'),
            self.perm('add'),
            self.perm('open'),
            self.perm('closed')
        })


class PermissionRequiredDecoratorTestCase(TestCase):
    
    #
    # The impact of altering the DJEM_DEFAULT_403 setting cannot be tested as
    # it is read at time of import of permission_required, so any test-based
    # setting override is not recognised.
    #
    
    def setUp(self):
        
        user = get_user_model().objects.create_user('test1')
        
        # Only grant a limited subset of permissions to test when model-level
        # permissions are NOT granted
        permissions = Permission.objects.filter(
            content_type__app_label='tests',
            content_type__model='olptest',
            codename__in=('open_olptest', 'combined_olptest')
        )
        
        user.user_permissions.set(permissions)
        
        self.user = user
        self.olptest_with_access = OLPTest.objects.create(user=user)
        self.olptest_without_access = OLPTest.objects.create()
        self.factory = RequestFactory()
    
    def test_unauthenticated(self):
        """
        Test the permission_required decorator with an unauthenticated user.
        Ensure the decorator correctly redirects to the login url.
        """
        
        view = permission_required(
            'tests.open_olptest'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_string_arg__access(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument.
        Ensure the decorator correctly allows access to the view for a user
        that has been granted that permission at the model level.
        """
        
        view = permission_required(
            'tests.open_olptest'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertContains(response, 'success', status_code=200)
    
    def test_string_arg__no_access__redirect(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        redirecting to the login page.
        """
        
        view = permission_required(
            'tests.add_olptest'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_string_arg__no_access__redirect__custom__relative(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument and a custom ``login_url`` is given as a
        relative url.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        redirecting to a custom page specified by the decorator.
        """
        
        view = permission_required(
            'tests.add_olptest',
            login_url='/custom/login/'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/login/?next=/test/'.format(settings.LOGIN_URL))
    
    def test_string_arg__no_access__redirect__custom__absolute(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument and a custom ``login_url`` is given as an
        absolute url.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        redirecting to a custom page specified by the decorator.
        """
        
        view = permission_required(
            'tests.add_olptest',
            login_url='https://example.com/custom/login/'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            'https://example.com/custom/login/?next=http%3A//testserver/test/'.format(
                settings.LOGIN_URL
            )
        )
    
    def test_string_arg__no_access__raise(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument and ``raise_exception`` given as True.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        raising PermissionDenied (which would be translated into a 403 error page).
        """
        
        view = permission_required(
            'tests.add_olptest',
            raise_exception=True
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(PermissionDenied):
            view(request)
    
    def test_string_arg__invalid_perm(self):
        """
        Test the permission_required decorator with an invalid permission as a
        single string argument.
        Ensure the decorator correctly denies access to the view.
        """
        
        view = permission_required(
            'fail'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_tuple_arg__access(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly allows access to the view for a user
        that has been granted that permission at the object level.
        """
        
        view = permission_required(
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertContains(response, 'success', status_code=200)
    
    def test_tuple_arg__no_access__redirect(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the object level, by
        redirecting to the login page.
        """
        
        view = permission_required(
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_tuple_arg__no_access__redirect__custom(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument and a custom ``login_url`` given.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the object level, by
        redirecting to a custom page specified by the decorator.
        """
        
        view = permission_required(
            ('tests.combined_olptest', 'obj'),
            login_url='/custom/login/'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/login/?next=/test/')
    
    def test_tuple_arg__no_access__raise(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument and ``raise_exception`` given as True.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the object level, by
        raising PermissionDenied (which would be translated into a 403 error page).
        """
        
        view = permission_required(
            ('tests.combined_olptest', 'obj'),
            raise_exception=True
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(PermissionDenied):
            view(request, obj=self.olptest_without_access.pk)
    
    def test_tuple_arg__invalid_perm(self):
        """
        Test the permission_required decorator with an invalid permission as a
        single tuple argument.
        Ensure the decorator correctly denies access to the view.
        """
        
        view = permission_required(
            ('fail', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_tuple_arg__invalid_object(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly raises a Http404 exception when an
        invalid object primary key is provided (which would be translated into
        a 404 error page).
        """
        
        view = permission_required(
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(Http404):
            view(request, obj=0)
    
    def test_multiple_args__access_all(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly allows access to the view for a user
        that has all appropriate permissions.
        """
        
        view = permission_required(
            'tests.open_olptest',
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertContains(response, 'success', status_code=200)
    
    def test_multiple_args__no_access__model(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the model-level permissions, by redirecting
        to the login page.
        """
        
        view = permission_required(
            'tests.add_olptest',
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_multiple_args__no_access__object(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the object-level permissions, by redirecting
        to the login page.
        """
        
        view = permission_required(
            'tests.open_olptest',
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_multiple_args__no_access__custom_redirect(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments, and a custom ``login_url``
        given.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the object-level permissions, by redirecting
        to a custom page specified by the decorator.
        """
        
        view = permission_required(
            'tests.open_olptest',
            ('tests.combined_olptest', 'obj'),
            login_url='/custom/login/'
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/login/?next=/test/')
    
    def test_multiple_args__no_access__raise(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the object-level permissions, by raising
        PermissionDenied (which would be translated into a 403 error page).
        """
        
        view = permission_required(
            'tests.open_olptest',
            ('tests.combined_olptest', 'obj'),
            raise_exception=True
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(PermissionDenied):
            view(request, obj=self.olptest_without_access.pk)
    
    def test_multiple_args__invalid_perm(self):
        """
        Test the permission_required decorator with multiple arguments, one
        of which contains an invalid permission.
        Ensure the decorator correctly denies access to the view.
        """
        
        view = permission_required(
            'tests.open_olptest',
            ('fail', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_multiple_args__invalid_object(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly returns a 404 error page when an invalid
        object primary key is provided (which would be translated into a 404
        error page).
        """
        
        view = permission_required(
            'tests.open_olptest',
            ('tests.combined_olptest', 'obj')
        )(_test_view)
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(Http404):
            view(request, obj=0)


class PermissionRequiredMixinTestCase(TestCase):
    
    #
    # The impact of altering the DJEM_DEFAULT_403 setting cannot be tested as
    # it is read at time of import of PermissionRequiredMixin, so any test-based
    # setting override is not recognised.
    #
    
    def setUp(self):
        
        user = get_user_model().objects.create_user('test1')
        
        # Only grant a limited subset of permissions to test when model-level
        # permissions are NOT granted
        permissions = Permission.objects.filter(
            content_type__app_label='tests',
            content_type__model='olptest',
            codename__in=('open_olptest', 'combined_olptest')
        )
        
        user.user_permissions.set(permissions)
        
        self.user = user
        self.olptest_with_access = OLPTest.objects.create(user=user)
        self.olptest_without_access = OLPTest.objects.create()
        self.factory = RequestFactory()
    
    def test_no_permissions(self):
        """
        Test the PermissionRequiredMixin with no defined permission_required.
        Ensure the mixin raises ImproperlyConfigured.
        """
        
        view = _TestView.as_view()
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        with self.assertRaises(ImproperlyConfigured):
            view(request)
    
    def test_unauthenticated(self):
        """
        Test the PermissionRequiredMixin with an unauthenticated user.
        Ensure the mixin correctly denies access to the view (the
        unauthenticated user having no permissions).
        """
        
        view = _TestView.as_view(
            permission_required='tests.open_olptest'
        )
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_string_arg__access(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        string.
        Ensure the mixin correctly allows access to the view for a user that
        has been granted that permission at the model level.
        """
        
        view = _TestView.as_view(
            permission_required='tests.open_olptest'
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertContains(response, 'success', status_code=200)
    
    def test_string_arg__no_access__redirect(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        string.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the model level, by redirecting
        to the login page.
        """
        
        view = _TestView.as_view(
            permission_required='tests.add_olptest'
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_string_arg__no_access__redirect__custom(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        string and a custom ``login_url``.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the model level, by redirecting
        to a custom page specified by ``login_url``.
        """
        
        view = _TestView.as_view(
            permission_required='tests.add_olptest',
            login_url='/custom/login/'
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/login/?next=/test/'.format(settings.LOGIN_URL))
    
    def test_string_arg__no_access__raise(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        string and a ``raise_exception`` set to True.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the model level, by raising
        PermissionDenied (which would be translated into a 403 error page).
        """
        
        view = _TestView.as_view(
            permission_required='tests.add_olptest',
            raise_exception=True
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(PermissionDenied):
            view(request)
    
    def test_string_arg__invalid_perm(self):
        """
        Test the PermissionRequiredMixin with an invalid permission as a single
        string.
        Ensure the mixin correctly denies access to the view.
        """
        
        view = _TestView.as_view(
            permission_required='fail'
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_tuple_arg__access(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a tuple.
        Ensure the mixin correctly allows access to the view for a user that
        has been granted that permission at the object level.
        """
        
        view = _TestView.as_view(
            permission_required=[('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertContains(response, 'success', status_code=200)
    
    def test_tuple_arg__no_access__redirect(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a tuple.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the object level, by
        redirecting to the login page.
        """
        
        view = _TestView.as_view(
            permission_required=[('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_tuple_arg__no_access__redirect__custom(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a tuple and
        a custom ``login_url``.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the object level, by
        to a custom page specified by ``login_url``.
        """
        
        view = _TestView.as_view(
            permission_required=[('tests.combined_olptest', 'obj')],
            login_url='/custom/login/'
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/login/?next=/test/')
    
    def test_tuple_arg__no_access__raise(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a tuple and
        ``raise_exception`` set to True.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the object level, by raising
        PermissionDenied (which would be translated into a 403 error page).
        """
        
        view = _TestView.as_view(
            permission_required=[('tests.combined_olptest', 'obj')],
            raise_exception=True
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(PermissionDenied):
            view(request, obj=self.olptest_without_access.pk)
    
    def test_tuple_arg__invalid_perm(self):
        """
        Test the PermissionRequiredMixin with an invalid permission as a tuple.
        Ensure the mixin correctly denies access to the view.
        """
        
        view = _TestView.as_view(
            permission_required=[('fail', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_tuple_arg__invalid_object(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a tuple.
        Ensure the mixin correctly raises a Http404 exception when an
        invalid object primary key is provided (which would be translated into
        a 404 error page).
        """
        
        view = _TestView.as_view(
            permission_required=[('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(Http404):
            view(request, obj=0)
    
    def test_multiple_args__access_all(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of strings and tuples.
        Ensure the mixin correctly allows access to the view for a user that
        has all appropriate permissions.
        """
        
        view = _TestView.as_view(
            permission_required=['tests.open_olptest', ('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertContains(response, 'success', status_code=200)
    
    def test_multiple_args__no_access__model(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of strings and tuples.
        Ensure the mixin correctly denies access to the view for a user that
        is missing one of the model-level permissions, by redirecting to the
        login page.
        """
        
        view = _TestView.as_view(
            permission_required=['tests.add_olptest', ('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_multiple_args__no_access__object(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments.
        Ensure the mixin correctly denies access to the view for a user that
        is missing one of the object-level permissions, by redirecting to the
        login page.
        """
        
        view = _TestView.as_view(
            permission_required=['tests.open_olptest', ('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_multiple_args__no_access__custom_redirect(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments, and a custom ``login_url``.
        Ensure the mixin correctly denies access to the view for a user that
        is missing one of the object-level permissions, by redirecting to a
        custom page specified by ``login_url``.
        """
        
        view = _TestView.as_view(
            permission_required=['tests.open_olptest', ('tests.combined_olptest', 'obj')],
            login_url='/custom/login/'
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_without_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/login/?next=/test/')
    
    def test_multiple_args__no_access__raise(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments, and ``raise_exception`` set to True.
        Ensure the mixin correctly denies access to the view for a user that is
        missing one of the object-level permissions, by raising PermissionDenied
        (which would be translated into a 403 error page).
        """
        
        view = _TestView.as_view(
            permission_required=['tests.open_olptest', ('tests.combined_olptest', 'obj')],
            raise_exception=True
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(PermissionDenied):
            view(request, obj=self.olptest_without_access.pk)
    
    def test_multiple_args__invalid_perm(self):
        """
        Test the PermissionRequiredMixin with multiple permissions as a mixture
        of strings and tuples, one of which is invalid.
        Ensure the mixin correctly denies access to the view.
        """
        
        view = _TestView.as_view(
            permission_required=['tests.open_olptest', ('fail', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        response = view(request, obj=self.olptest_with_access.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '{0}?next=/test/'.format(settings.LOGIN_URL))
    
    def test_multiple_args__invalid_object(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of strings and tuples.
        Ensure the mixin correctly raises a Http404 exception when an
        invalid object primary key is provided (which would be translated into
        a 404 error page).
        """
        
        view = _TestView.as_view(
            permission_required=['tests.open_olptest', ('tests.combined_olptest', 'obj')]
        )
        
        request = self.factory.get('/test/')
        request.user = self.user  # simulate login
        
        with self.assertRaises(Http404):
            view(request, obj=0)
