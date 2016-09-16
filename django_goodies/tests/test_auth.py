from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.test import TestCase

from .app.models import ArchivableTest, OPTest


class ObjectPermissionsTestCase(TestCase):
    
    def setUp(self):
        
        group1 = Group.objects.create(name='Test Group 1')
        group2 = Group.objects.create(name='Test Group 2')
        
        user1 = get_user_model().objects.create_user('test1')
        user1.groups.add(group1)
        
        user2 = get_user_model().objects.create_user('test2')
        user2.groups.add(group2)
        
        # Grant both users and both groups all permissions for OPTest
        permissions = Permission.objects.filter(
            content_type__app_label='app',
            content_type__model='optest'
        )
        
        user1.user_permissions.set(permissions)
        user2.user_permissions.set(permissions)
        group1.permissions.set(permissions)
        group2.permissions.set(permissions)
        
        self.user1 = user1
        self.user2 = user2
        self.group1 = group1
        self.group2 = group2
        self.all_permissions = permissions
    
    def test_has_perm__no_model_level(self):
        """
        Test a user is denied object-level permissions if they don't have the
        corresponding model-level permissions.
        """
        
        obj = OPTest.objects.create()
        
        user1 = get_user_model().objects.create_user('useless')
        perm1 = user1.has_perm('app.view_optest', obj)
        self.assertFalse(perm1)
        
        user2 = get_user_model().objects.create_user('useful')
        user2.user_permissions.add(Permission.objects.get(codename='view_optest'))
        perm2 = user2.has_perm('app.view_optest', obj)
        self.assertTrue(perm2)
    
    def test_has_perm__inactive_user(self):
        """
        Test an inactive user is denied object-level permissions without ever
        reaching the object's permission access method.
        """
        
        user = get_user_model().objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Grant the user the "change_optest" permission to ensure it is their
        # inactive-ness that denies them permission
        user.user_permissions.add(Permission.objects.get(codename='change_optest'))
        
        obj = OPTest.objects.create()
        
        perm = user.has_perm('app.change_optest', obj)
        
        self.assertFalse(perm)
    
    def test_has_perm__super_user(self):
        """
        Test a superuser is granted object-level permissions without ever
        reaching the object's permission access method.
        """
        
        user = get_user_model().objects.create_user('super')
        user.is_superuser = True
        user.save()
        
        # Deliberately do not grant the user the "change_optest" permission to
        # ensure it is their super-ness that grants them permission
        
        obj = OPTest.objects.create()
        
        perm = user.has_perm('app.change_optest', obj)
        
        self.assertTrue(perm)
    
    def test_has_perm__no_access_fn(self):
        """
        Test that the lack of defined permission access functions on the object
        being tested denies access.
        """
        
        obj = OPTest.objects.create()
        
        perm = self.user1.has_perm('app.add_optest', obj)
        
        self.assertFalse(perm)
    
    def test_has_perm__wrong_object(self):
        """
        Test that checking a real permission but on the wrong object denies
        access.
        """
        
        obj = ArchivableTest.objects.create()
        
        perm = self.user1.has_perm('app.change_optest', obj)
        
        self.assertFalse(perm)
    
    def test_has_perm__user_grants_permission(self):
        """
        Test that an object's user-based permission access method can be used
        to grant permissions to some users and not others, when all users have
        the same permission at the model level.
        """
        
        obj = OPTest.objects.create(user=self.user1)
        
        perm1 = self.user1.has_perm('app.delete_optest', obj)
        perm2 = self.user2.has_perm('app.delete_optest', obj)
        
        self.assertTrue(perm1)
        self.assertFalse(perm2)
    
    def test_has_perm__group_grants_permission(self):
        """
        Test that an object's group-based permission access method can be used
        to grant permissions to some users and not others based on their
        groups, when all groups have the same permission at the model level.
        """
        
        obj = OPTest.objects.create(group=self.group1)
        
        perm1 = self.user1.has_perm('app.delete_optest', obj)
        perm2 = self.user2.has_perm('app.delete_optest', obj)
        
        self.assertTrue(perm1)
        self.assertFalse(perm2)
    
    def test_has_perm__neither_grant_permission(self):
        """
        Test that an object's permission access methods can be used to deny
        permissions to users that fail both the user-based and group-based tests.
        """
        
        obj = OPTest.objects.create()
        
        perm1 = self.user1.has_perm('app.delete_optest', obj)
        perm2 = self.user2.has_perm('app.delete_optest', obj)
        
        self.assertFalse(perm1)
        self.assertFalse(perm2)
    
    def test_has_perm__cache(self):
        """
        Test that determining a user's object-level permission creates a cache
        on the User instance of the result, for the permission and object tested.
        """
        
        user = self.user1
        obj = OPTest.objects.create()
        perm_cache_name = 'perm_cache_app.delete_optest_{0}'.format(obj.pk)
        user_perm_cache_name = '_user_{0}'.format(perm_cache_name)
        group_perm_cache_name = '_group_{0}'.format(perm_cache_name)
        
        # Test cache does not exist
        with self.assertRaises(AttributeError):
            getattr(user, user_perm_cache_name)
        
        with self.assertRaises(AttributeError):
            getattr(user, group_perm_cache_name)
        
        user.has_perm('app.delete_optest', obj)
        
        # Test cache has been set
        self.assertFalse(getattr(user, user_perm_cache_name))
        self.assertFalse(getattr(user, group_perm_cache_name))
        
        # Test requerying for the user resets the cache
        user = get_user_model().objects.get(pk=user.pk)
        
        with self.assertRaises(AttributeError):
            getattr(user, user_perm_cache_name)
        
        with self.assertRaises(AttributeError):
            getattr(user, group_perm_cache_name)
    
    def test_has_perms(self):
        """
        Test PermissionsMixin.has_perms works and correctly identifies the
        object-level permissions the user has.
        """
        
        obj = OPTest.objects.create(user=self.user1)
        
        perm1 = self.user1.has_perms(('app.change_optest', 'app.add_optest'), obj)
        self.assertFalse(perm1)
        
        perm2 = self.user1.has_perms(('app.change_optest', 'app.delete_optest'), obj)
        self.assertTrue(perm2)
    
    def test_get_group_permissions(self):
        """
        Test PermissionsMixin.get_group_permissions works and correctly
        identifies the object-level permissions the user has.
        """
        
        obj = OPTest.objects.create(group=self.group1)
        
        perms1 = self.user1.get_group_permissions(obj)
        self.assertEquals(perms1, set((
            'app.view_optest', 'app.delete_optest'
        )))
        
        perms2 = self.user2.get_group_permissions(obj)
        self.assertEquals(perms2, set(('app.view_optest',)))
    
    def test_get_group_permissions__inactive_user(self):
        """
        Test PermissionsMixin.get_group_permissions correctly denies all
        permissions to inactive users.
        """
        
        user = get_user_model().objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = OPTest.objects.create()
        
        perms = user.get_group_permissions(obj)
        self.assertEquals(perms, set())
    
    def test_get_group_permissions__super_user(self):
        """
        Test PermissionsMixin.get_group_permissions correctly grants all
        permissions to superusers.
        """
        
        user = get_user_model().objects.create_user('inactive')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them permission
        
        obj = OPTest.objects.create()
        
        perms = user.get_group_permissions(obj)
        self.assertEquals(perms, set((
            'app.view_optest', 'app.add_optest', 'app.change_optest', 'app.delete_optest'
        )))
    
    def test_get_group_permissions__cache(self):
        """
        Test that PermissionsMixin.get_group_permissions correctly creates a
        a cache on the User instance of the result of each permission test, for
        the permission and object tested.
        """
        
        user = self.user1
        obj = OPTest.objects.create()
        
        expected_caches = (
            '_group_perm_cache_app.view_optest_{0}',
            '_group_perm_cache_app.add_optest_{0}',
            '_group_perm_cache_app.change_optest_{0}',
            '_group_perm_cache_app.delete_optest_{0}',
        )
        
        expected_caches = [s.format(obj.pk) for s in expected_caches]
        
        # Test caches do not exist
        for cache_attr in expected_caches:
            with self.assertRaises(AttributeError):
                getattr(user, cache_attr)
        
        user.get_group_permissions(obj)
        
        # Test caches have been set
        for cache_attr in expected_caches:
            try:
                getattr(user, cache_attr)
            except AttributeError:
                self.fail('Cache not set: {0}'.format(cache_attr))
        
        # Test requerying for the user resets the cache
        user = get_user_model().objects.get(pk=user.pk)
        for cache_attr in expected_caches:
            with self.assertRaises(AttributeError):
                getattr(user, cache_attr)
    
    def test_get_all_permissions(self):
        """
        Test PermissionsMixin.get_all_permissions works and correctly
        identifies the object-level permissions the user has.
        """
        
        obj = OPTest.objects.create(group=self.group1)
        
        perms1 = self.user1.get_all_permissions(obj)
        self.assertEquals(perms1, set((
            'app.view_optest', 'app.change_optest', 'app.delete_optest'
        )))
        
        perms2 = self.user2.get_all_permissions(obj)
        self.assertEquals(perms2, set(('app.view_optest', 'app.change_optest')))
    
    def test_get_all_permissions__inactive_user(self):
        """
        Test PermissionsMixin.get_all_permissions correctly denies all
        permissions to inactive users.
        """
        
        user = get_user_model().objects.create_user('inactive')
        user.is_active = False
        user.save()
        
        # Give the user all model-level permissions to ensure it is the
        # inactive-ness that denies them permission
        user.user_permissions.set(self.all_permissions)
        
        obj = OPTest.objects.create()
        
        perms = user.get_all_permissions(obj)
        self.assertEquals(perms, set())
    
    def test_get_all_permissions__super_user(self):
        """
        Test PermissionsMixin.get_all_permissions correctly grants all
        permissions to superusers.
        """
        
        user = get_user_model().objects.create_user('inactive')
        user.is_superuser = True
        user.save()
        
        # The user deliberately does not have any model-level permissions to
        # ensure it is the super-ness that grants them permission
        
        obj = OPTest.objects.create()
        
        perms = user.get_all_permissions(obj)
        self.assertEquals(perms, set((
            'app.view_optest', 'app.add_optest', 'app.change_optest', 'app.delete_optest'
        )))
    
    def test_get_all_permissions__cache(self):
        """
        Test that PermissionsMixin.get_group_permissions correctly creates a
        a cache on the User instance of the result of each permission test, for
        the permission and object tested.
        """
        
        user = self.user1
        obj = OPTest.objects.create()
        
        expected_caches = (
            '_user_perm_cache_app.view_optest_{0}',  # group won't need checking
            '_user_perm_cache_app.add_optest_{0}',
            '_group_perm_cache_app.add_optest_{0}',
            '_user_perm_cache_app.change_optest_{0}',  # group won't need checking
            '_user_perm_cache_app.delete_optest_{0}',
            '_group_perm_cache_app.delete_optest_{0}',
        )
        
        expected_caches = [s.format(obj.pk) for s in expected_caches]
        
        # Test caches do not exist
        for cache_attr in expected_caches:
            with self.assertRaises(AttributeError):
                getattr(user, cache_attr)
        
        user.get_all_permissions(obj)
        
        # Test caches have been set
        for cache_attr in expected_caches:
            try:
                getattr(user, cache_attr)
            except AttributeError:
                self.fail('Cache not set: {0}'.format(cache_attr))
        
        # Test requerying for the user resets the cache
        user = get_user_model().objects.get(pk=user.pk)
        for cache_attr in expected_caches:
            with self.assertRaises(AttributeError):
                getattr(user, cache_attr)


class PermissionRequiredDecoratorTestCase(TestCase):
    
    def setUp(self):
        
        user = get_user_model().objects.create_user('test1')
        user.set_password('blahblahblah')
        user.save()
        
        # Grant user permission to view, change and delete OPTest records, but
        # not add them
        permissions = Permission.objects.filter(
            content_type__app_label='app',
            content_type__model='optest',
            codename__in=('view_optest', 'change_optest', 'delete_optest')
        )
        
        user.user_permissions.set(permissions)
        
        self.user = user
        self.optest_with_access = OPTest.objects.create(user=user)
        self.optest_without_access = OPTest.objects.create()
    
    def test_unauthenticated(self):
        """
        Test the permission_required decorator with an unauthenticated user.
        Ensure the decorator correctly redirects to the login url.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__string__delete', args=(optest.pk,))
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_string_arg__access(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument.
        Ensure the decorator correctly allows access to the view for a user
        that has been granted that permission at the model level.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__string__delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'success')
    
    def test_string_arg__no_access__redirect(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        redirecting to the login page.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__string__add', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_string_arg__no_access__redirect__custom(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        redirecting to a custom page specified by the decorator.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__string__add__custom_redir', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '/custom/?next={0}'.format(url))
    
    def test_string_arg__no_access__403(self):
        """
        Test the permission_required decorator with a valid permission as a
        single string argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the model level, by
        displaying a 403 error page.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__string__add__raise', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 403)
    
    def test_string_arg__invalid_perm(self):
        """
        Test the permission_required decorator with an invalid permission as a
        single string argument.
        Ensure the decorator correctly denies access to the view.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__string__invalid', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_tuple_arg__access(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly allows access to the view for a user
        that has been granted that permission at the object level.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__tuple', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'success')
    
    def test_tuple_arg__no_access__redirect(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the object level, by
        redirecting to the login page.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__tuple', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_tuple_arg__no_access__redirect__custom(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the object level, by
        redirecting to a custom page specified by the decorator.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__tuple__custom_redir', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '/custom/?next={0}'.format(url))
    
    def test_tuple_arg__no_access__403(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly denies access to the view for a user
        that has not been granted that permission at the object level, by
        displaying a 403 error page.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__tuple__raise', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 403)
    
    def test_tuple_arg__invalid_perm(self):
        """
        Test the permission_required decorator with an invalid permission as a
        single tuple argument.
        Ensure the decorator correctly denies access to the view.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__tuple__invalid', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_tuple_arg__invalid_object(self):
        """
        Test the permission_required decorator with a valid permission as a
        single tuple argument.
        Ensure the decorator correctly returns a 404 error page when an invalid
        object primary key is provided in the URL.
        """
        
        url = reverse('perm_decorator__tuple', args=(0,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 404)
    
    def test_multiple_args__access_all(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly allows access to the view for a user
        that has all appropriate permissions.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__multiple__view_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'success')
    
    def test_multiple_args__no_access__model(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the model-level permissions, by redirecting
        to the login page.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_decorator__multiple__add_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_multiple_args__no_access__object(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the object-level permissions, by redirecting
        to the login page.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__multiple__view_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_multiple_args__no_access__redir__custom(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the object-level permissions, by redirecting
        to a custom page specified by the decorator.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__multiple__view_delete__custom_redir', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '/custom/?next={0}'.format(url))
    
    def test_multiple_args__no_access__403(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly denies access to the view for a user
        that has is missing one of the object-level permissions, by displaying
        a 403 error page.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__multiple__view_delete__raise', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 403)
    
    def test_multiple_args__invalid_perm(self):
        """
        Test the permission_required decorator with multiple arguments, one
        of which contains an invalid permission.
        Ensure the decorator correctly denies access to the view.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_decorator__multiple__view_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_multiple_args__invalid_object(self):
        """
        Test the permission_required decorator with multiple valid permissions
        as a mixture of string and tuple arguments.
        Ensure the decorator correctly returns a 404 error page when an invalid
        object primary key is provided in the URL.
        """
        
        url = reverse('perm_decorator__multiple__view_delete', args=(0,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 404)


class PermissionRequiredMixinTestCase(TestCase):
    
    #
    # Note: Unlike the permission_required decorator tests, these mixin tests
    # do not test raise_exception or changing the login_url, as the mixin
    # doesn't actually contain any of the implementation for this.
    #
    
    def setUp(self):
        
        user = get_user_model().objects.create_user('test1')
        user.set_password('blahblahblah')
        user.save()
        
        # Grant user permission to view, change and delete OPTest records, but
        # not add them
        permissions = Permission.objects.filter(
            content_type__app_label='app',
            content_type__model='optest',
            codename__in=('view_optest', 'change_optest', 'delete_optest')
        )
        
        user.user_permissions.set(permissions)
        
        self.user = user
        self.optest_with_access = OPTest.objects.create(user=user)
        self.optest_without_access = OPTest.objects.create()
    
    def test_no_permissions(self):
        """
        Test the PermissionRequiredMixin with no defined permission_required.
        Ensure the mixin raises ImproperlyConfigured.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__unconfigured', args=(optest.pk,))
        
        with self.assertRaises(ImproperlyConfigured):
            self.client.get(url, follow=True)
    
    def test_unauthenticated(self):
        """
        Test the PermissionRequiredMixin with an unauthenticated user.
        Ensure the mixin correctly denies access to the view (the
        unauthenticated user having no permissions).
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__string__delete', args=(optest.pk,))
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_string_arg__access(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        string argument.
        Ensure the mixin correctly allows access to the view for a user that
        has been granted that permission at the model level.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__string__delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'success')
    
    def test_string_arg__no_access(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        string argument.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the model level, by redirecting
        to the login page.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__string__add', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_string_arg__invalid_perm(self):
        """
        Test the PermissionRequiredMixin with an invalid permission as a single
        string argument.
        Ensure the mixin correctly denies access to the view.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__string__invalid', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_tuple_arg__access(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        tuple argument.
        Ensure the mixin correctly allows access to the view for a user that
        has been granted that permission at the object level.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__tuple', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'success')
    
    def test_tuple_arg__no_access(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        tuple argument.
        Ensure the mixin correctly denies access to the view for a user that
        has not been granted that permission at the object level, by
        redirecting to the login page.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_mixin__tuple', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_tuple_arg__invalid_perm(self):
        """
        Test the PermissionRequiredMixin with an invalid permission as a single
        tuple argument.
        Ensure the mixin correctly denies access to the view.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__tuple__invalid', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_tuple_arg__invalid_object(self):
        """
        Test the PermissionRequiredMixin with a valid permission as a single
        tuple argument.
        Ensure the mixin correctly returns a 404 error page when an invalid
        object primary key is provided in the URL.
        """
        
        url = reverse('perm_mixin__tuple', args=(0,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 404)
    
    def test_multiple_args__access_all(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments.
        Ensure the mixin correctly allows access to the view for a user that
        has all appropriate permissions.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__multiple__view_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'success')
    
    def test_multiple_args__no_access__model(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments.
        Ensure the mixin correctly denies access to the view for a user that
        has is missing one of the model-level permissions, by redirecting to
        the login page.
        """
        
        optest = self.optest_with_access
        url = reverse('perm_mixin__multiple__add_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_multiple_args__no_access__object(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments.
        Ensure the mixin correctly denies access to the view for a user that
        has is missing one of the object-level permissions, by redirecting to
        the login page.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_mixin__multiple__view_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_multiple_args__invalid_perm(self):
        """
        Test the PermissionRequiredMixin with multiple arguments, one of which
        contains an invalid permission.
        Ensure the mixin correctly denies access to the view.
        """
        
        optest = self.optest_without_access
        url = reverse('perm_mixin__multiple__view_delete', args=(optest.pk,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertRedirects(response, '{0}?next={1}'.format(settings.LOGIN_URL, url))
    
    def test_multiple_args__invalid_object(self):
        """
        Test the PermissionRequiredMixin with multiple valid permissions as a
        mixture of string and tuple arguments.
        Ensure the mixin correctly returns a 404 error page when an invalid
        object primary key is provided in the URL.
        """
        
        url = reverse('perm_mixin__multiple__view_delete', args=(0,))
        
        self.client.login(username='test1', password='blahblahblah')
        
        response = self.client.get(url, follow=True)
        
        self.assertEquals(response.status_code, 404)
