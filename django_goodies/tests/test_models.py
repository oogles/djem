import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

import pytz

from django_goodies.models import TimeZoneField
from django_goodies.utils.dt import TimeZoneHelper

from .app.models import (
    ArchivableTest, CommonInfoTest, StaticTest, TimeZoneTest, VersioningTest
)


def make_user(username):
    
    return get_user_model().objects.create_user(username, 'fakepassword')


class CommonInfoTestCase(TestCase):
    """
    Tests the behaviour of the ``CommonInfoMixin`` class, when mixed into a
    model.
    """
    
    def setUp(self):
        
        self.user1 = make_user('test')
        self.user2 = make_user('test2')
    
    def test_object_save__no_user__required(self):
        """
        Test the overridden ``save`` method correctly raises TypeError when
        the ``user`` argument is not provided and it is required (per
        ``GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE`` setting).
        """
        
        obj = CommonInfoTest()
        
        with self.assertRaises(TypeError):
            obj.save()
    
    def test_object_save__no_user__not_required(self):
        """
        Test the overridden ``save`` method correctly accepts a null ``user``
        argument when it is not required (per``GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE``
        setting). Instance creation should fail on missing fields as they are
        not automatically populated by the given user.
        """
        
        obj = CommonInfoTest()
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            with self.assertRaises(IntegrityError):
                obj.save()
    
    def test_object_create__user__required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when creating a new instance, passing the ``user`` argument
        when it is required.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user1)
        
        # Test the object attributes are updated
        self.assertEquals(obj.user_created_id, self.user1.pk)
        self.assertEquals(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEquals(obj.date_created, obj.date_modified)
        
        # Test the changes are correctly written to the database
        obj = CommonInfoTest.objects.get(pk=obj.pk)
        
        self.assertEquals(obj.user_created_id, self.user1.pk)
        self.assertEquals(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEquals(obj.date_created, obj.date_modified)
        
        self.assertNumQueries(2)
    
    def test_object_create__user__not_required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when creating a new instance, passing the ``user`` argument
        when it is not required. This should be identical to passing it when
        it is required.
        """
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            self.test_object_create__user__required()
    
    def test_object_create__no_user(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when creating a new instance, not using the ``user`` argument.
        """
        
        user = self.user1
        obj = CommonInfoTest(user_created=user, user_modified=user)
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            obj.save()
        
        # Test the object attributes are updated/not updated as necessary
        self.assertEquals(obj.user_created_id, user.pk)
        self.assertEquals(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEquals(obj.date_created, obj.date_modified)
        
        # Test the changes are correctly written to the database
        obj = CommonInfoTest.objects.get(pk=obj.pk)
        
        self.assertEquals(obj.user_created_id, user.pk)
        self.assertEquals(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEquals(obj.date_created, obj.date_modified)
        
        self.assertNumQueries(2)
    
    def test_object_create__existing_date_created(self):
        """
        Test the overridden ``save`` method maintains a ``date_created`` value if
        one already exists when creating a new instance.
        """
        
        d = timezone.now() - datetime.timedelta(days=5)
        
        obj = CommonInfoTest(date_created=d)
        obj.save(self.user1)
        
        # Test the object attributes are updated
        self.assertEquals(obj.date_created, d)
        
        # Test the changes are correctly written to the database
        obj = CommonInfoTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.date_created, d)
        
        self.assertNumQueries(1)
    
    def test_object_create__existing_user_created(self):
        """
        Test the overridden ``save`` method maintains a ``user_created`` value if
        one already exists when creating a new instance.
        """
        
        obj = CommonInfoTest(user_created=self.user2)
        obj.save(self.user1)
        
        # Test the object attributes are updated
        self.assertEquals(obj.user_created_id, self.user2.pk)
        self.assertEquals(obj.user_modified_id, self.user1.pk)
        
        # Test the changes are correctly written to the database
        obj = CommonInfoTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.user_created_id, self.user2.pk)
        self.assertEquals(obj.user_modified_id, self.user1.pk)
        
        self.assertNumQueries(1)
    
    def test_object_update__user__required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when updating an existing instance, passing the ``user`` argument
        when it is required.
        """
        
        obj1 = CommonInfoTest()
        obj1.save(self.user1)
        
        obj2 = CommonInfoTest.objects.get(pk=obj1.pk)
        obj2.save(self.user2, update_fields=('test',))
        
        # Test the object attributes are updated
        self.assertEquals(obj2.user_created_id, self.user1.pk)
        self.assertEquals(obj2.user_modified_id, self.user2.pk)
        
        self.assertEquals(obj1.date_created, obj2.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
        
        # Test the changes are correctly written to the database
        obj2 = CommonInfoTest.objects.get(pk=obj2.pk)
        
        self.assertEquals(obj2.user_created_id, self.user1.pk)
        self.assertEquals(obj2.user_modified_id, self.user2.pk)
        
        self.assertEquals(obj1.date_created, obj2.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
        
        self.assertNumQueries(3)
    
    def test_object_update__user__not_required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when updating an existing instance, passing the ``user`` argument
        when it is not required. This should be identical to passing it when
        it is required.
        """
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            self.test_object_update__user__required()
    
    def test_object_update__no_user(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when updating an existing instance, not passing the ``user``
        argument.
        """
        
        user = self.user1
        
        obj1 = CommonInfoTest()
        obj1.save(user)
        
        obj2 = CommonInfoTest.objects.get(pk=obj1.pk)
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            obj2.save(update_fields=('test',))
        
        # Test the object attributes are updated/not updated as necessary
        self.assertEquals(obj2.user_created_id, user.pk)
        self.assertEquals(obj2.user_modified_id, user.pk)
        
        self.assertEquals(obj1.date_created, obj2.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
        
        # Test the changes are correctly written to the database
        obj2 = CommonInfoTest.objects.get(pk=obj2.pk)
        
        self.assertEquals(obj2.user_created_id, user.pk)
        self.assertEquals(obj2.user_modified_id, user.pk)
        
        self.assertEquals(obj1.date_created, obj2.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
        
        self.assertNumQueries(3)
    
    def test_queryset_update__user__required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        passing the ``user`` argument when it is required.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user1)
        date_modified = obj.date_modified
        
        self.assertEquals(CommonInfoTest.objects.filter(user_modified=self.user1).count(), 1)
        
        CommonInfoTest.objects.all().update(self.user2, test=False)
        
        self.assertEquals(CommonInfoTest.objects.filter(user_modified=self.user2).count(), 1)
        self.assertGreater(CommonInfoTest.objects.first().date_modified, date_modified)
        
        self.assertNumQueries(5)
    
    def test_queryset_update__user__not_required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        passing the ``user`` argument when it is not required. This should be
        identical to passing it when it is required.
        """
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            self.test_queryset_update__user__required()
    
    def test_queryset_update__no_user__required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        not passing the ``user`` argument when it is required.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user1)
        
        with self.assertRaises(TypeError):
            CommonInfoTest.objects.all().update(test=False)
        
        self.assertNumQueries(1)
    
    def test_queryset_update__no_user__not_required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        not passing the ``user`` argument when it is not required.
        """
        
        user = self.user1
        
        obj = CommonInfoTest()
        obj.save(user)
        date_modified = obj.date_modified
        
        self.assertEquals(CommonInfoTest.objects.filter(user_modified=user).count(), 1)
        
        with self.settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            CommonInfoTest.objects.all().update(test=False)
        
        self.assertEquals(CommonInfoTest.objects.filter(user_modified=user).count(), 1)
        self.assertGreater(CommonInfoTest.objects.first().date_modified, date_modified)
        
        self.assertNumQueries(5)
    
    def test_manager_update(self):
        """
        Test the overridden ``update`` method of the custom queryset, accessed
        from the custom manager.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user1)
        date_modified = obj.date_modified
        
        self.assertEquals(CommonInfoTest.objects.filter(user_modified=self.user1).count(), 1)
        
        CommonInfoTest.objects.update(self.user2, test=False)
        
        self.assertEquals(CommonInfoTest.objects.filter(user_modified=self.user2).count(), 1)
        self.assertGreater(CommonInfoTest.objects.first().date_modified, date_modified)
        
        self.assertNumQueries(5)
    
    def test_object_owned_by(self):
        """
        Test the ``owned_by`` method of a model instance.
        """
        
        obj1 = CommonInfoTest()
        obj1.save(self.user1)
        
        obj2 = CommonInfoTest()
        obj2.save(self.user2)
        
        self.assertTrue(obj1.owned_by(self.user1))
        self.assertTrue(obj1.owned_by(self.user1.pk))
        self.assertFalse(obj1.owned_by(self.user2))
        
        self.assertTrue(obj2.owned_by(self.user2))
        self.assertTrue(obj2.owned_by(self.user2.pk))
        self.assertFalse(obj2.owned_by(self.user1))
        
        self.assertNumQueries(2)
    
    def test_queryset_owned_by(self):
        """
        Test the ``owned_by`` method of the custom queryset.
        """
        
        CommonInfoTest().save(self.user1)
        CommonInfoTest().save(self.user2)
        
        self.assertEquals(CommonInfoTest.objects.count(), 2)
        
        qs = CommonInfoTest.objects.all()
        
        self.assertEquals(qs.owned_by(self.user1).count(), 1)
        self.assertEquals(qs.owned_by(self.user1.pk).count(), 1)
        self.assertEquals(qs.filter(test=False).owned_by(self.user1).count(), 0)
        self.assertEquals(qs.owned_by(self.user1).owned_by(self.user2).count(), 0)
        
        self.assertNumQueries(7)
    
    def test_manager_owned_by(self):
        """
        Test the ``owned_by`` method of the custom queryset, accessed from the
        manager.
        """
        
        CommonInfoTest().save(self.user1)
        CommonInfoTest().save(self.user2)
        
        self.assertEquals(CommonInfoTest.objects.count(), 2)
        
        # Test owned_by with user object
        self.assertEquals(CommonInfoTest.objects.owned_by(self.user1).count(), 1)
        self.assertEquals(CommonInfoTest.objects.owned_by(self.user2).count(), 1)
        
        # Test owned_by with user id
        self.assertEquals(CommonInfoTest.objects.owned_by(self.user1.pk).count(), 1)
        self.assertEquals(CommonInfoTest.objects.owned_by(self.user2.pk).count(), 1)
        
        self.assertNumQueries(7)
    
    def test_object_permissions__change(self):
        """
        Test the out-of-the-box implementation of object-level "change"
        permissions using ``owned_by``.
        """
        
        user = self.user1
        
        # Add model-level permission to ensure it is object-level permissions
        # being granted/denied
        user.user_permissions.add(Permission.objects.get(codename='change_commoninfotest'))
        
        obj = CommonInfoTest()
        obj.save(user)
        
        self.assertTrue(user.has_perm('app.change_commoninfotest', obj))
        self.assertFalse(self.user2.has_perm('app.change_commoninfotest', obj))
    
    def test_object_permissions__delete(self):
        """
        Test the out-of-the-box implementation of object-level "delete"
        permissions using ``owned_by``.
        """
        
        user = self.user1
        
        # Add model-level permission to ensure it is object-level permissions
        # being granted/denied
        user.user_permissions.add(Permission.objects.get(codename='delete_commoninfotest'))
        
        obj = CommonInfoTest()
        obj.save(user)
        
        self.assertTrue(user.has_perm('app.delete_commoninfotest', obj))
        self.assertFalse(self.user2.has_perm('app.delete_commoninfotest', obj))


class ArchivableTestCase(TestCase):
    """
    Tests the behaviour of the ``ArchivableMixin`` class, when mixed into a
    model.
    """
    
    def setUp(self):
        
        self.obj1 = ArchivableTest.objects.create(is_archived=True)
        self.obj2 = ArchivableTest.objects.create(is_archived=False)
    
    def test_managers_archived_flag(self):
        """
        Test the ``archived`` flag for the three managers - ``objects``,
        ``live`` and ``archived`` - behaves properly and the managers
        return the correct initial querysets.
        """
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        self.assertNumQueries(3)
    
    def test_object_archive__no_args(self):
        """
        Test the ``archive`` method of an instance, when called with no
        arguments.
        """
        
        self.assertFalse(self.obj2.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        self.obj2.archive()
        
        self.assertTrue(self.obj2.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 0)
        self.assertEquals(ArchivableTest.archived.count(), 2)
        
        self.assertNumQueries(7)
    
    def test_object_archive__args(self):
        """
        Test the ``archive`` method of an instance, when called with the
        ``update_fields`` argument subsequently passed to its call to ``save``.
        """
        
        self.assertFalse(self.obj2.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        self.obj2.archive(update_fields=('test',))
        
        self.assertTrue(self.obj2.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 0)
        self.assertEquals(ArchivableTest.archived.count(), 2)
        
        self.assertNumQueries(7)
    
    def test_object_unarchive__no_args(self):
        """
        Test the ``unarchive`` method of an instance, when called with no
        arguments.
        """
        
        self.assertTrue(self.obj1.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        self.obj1.unarchive()
        
        self.assertFalse(self.obj1.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 2)
        self.assertEquals(ArchivableTest.archived.count(), 0)
        
        self.assertNumQueries(7)
    
    def test_object_unarchive__args(self):
        """
        Test the ``unarchive`` method of an instance, when called with the
        ``update_fields`` argument subsequently passed to its call to ``save``.
        """
        
        self.assertTrue(self.obj1.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        self.obj1.unarchive(update_fields=('test',))
        
        self.assertFalse(self.obj1.is_archived)
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 2)
        self.assertEquals(ArchivableTest.archived.count(), 0)
        
        self.assertNumQueries(7)
    
    def test_queryset_archive(self):
        """
        Test the custom queryset ``archive`` method correctly archives all
        records in the queryset.
        """
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        ArchivableTest.objects.all().archive()
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 0)
        self.assertEquals(ArchivableTest.archived.count(), 2)
        
        self.assertNumQueries(7)
    
    def test_queryset_unarchive(self):
        """
        Test the custom queryset ``unarchive`` method correctly unarchives all
        records in the queryset.
        """
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 1)
        self.assertEquals(ArchivableTest.archived.count(), 1)
        
        ArchivableTest.objects.all().unarchive()
        
        self.assertEquals(ArchivableTest.objects.count(), 2)
        self.assertEquals(ArchivableTest.live.count(), 2)
        self.assertEquals(ArchivableTest.archived.count(), 0)
        
        self.assertNumQueries(7)
    
    def test_manager_archive_access(self):
        """
        Test that the custom ``ArchivableManager`` used by ``ArchivableMixin``
        does not provide direct access to the custom ``archive`` method
        defined on the ``ArchivableQuerySet`` the manager is based on.
        """
        
        with self.assertRaises(AttributeError):
            ArchivableTest.objects.archive()
        
        self.assertNumQueries(0)
    
    def test_manager_unarchive_access(self):
        """
        Test that the custom ``ArchivableManager`` used by ``ArchivableMixin``
        does not provide direct access to the custom ``unarchive`` method
        defined on the ``ArchivableQuerySet`` the manager is based on.
        """
        
        with self.assertRaises(AttributeError):
            ArchivableTest.objects.unarchive()
        
        self.assertNumQueries(0)


class VersioningTestCase(TestCase):
    """
    Tests the behaviour of the ``VersioningMixin`` class, when mixed into a
    model.
    """
    
    def test_save_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``save``
        method on a model instance is called.
        """
        
        obj = VersioningTest.objects.create()
        
        # Test default value set correctly on object
        self.assertEquals(obj.version, 1)
        
        # Test default value correctly saved to the database without increment
        obj = VersioningTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 1)
        
        # Increment value
        obj.save(update_fields=('test',))
        
        # Test incremented value correctly saved to the database
        obj = VersioningTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 2)
        
        self.assertNumQueries(4)
    
    def test_multiple_save_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``save``
        method on a model instance is called multiple times.
        """
        
        obj = VersioningTest.objects.create()  # version 1
        
        obj.save()  # version 2
        obj.save()  # version 3
        
        # Test incremented value correctly saved to the database
        obj = VersioningTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 3)
        
        self.assertNumQueries(4)
    
    def test_version_inaccessible_after_increment(self):
        """
        Test the version field is no longer accessible after it has been
        atomically incremented.
        """
        
        obj = VersioningTest.objects.create()
        
        # Increment value
        obj.save()
        
        # New version cannot be known on the same instance - it has to be
        # requeried
        with self.assertRaises(VersioningTest.AmbiguousVersionError):
            bool(obj.version)  # bool() used purely to force evaluation of SimpleLazyObject
        
        self.assertNumQueries(2)
    
    def test_manager_update_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``update``
        method on a model manager is called.
        """
        
        obj = VersioningTest.objects.create()
        
        # Test default value set correctly
        self.assertEquals(obj.version, 1)
        
        # Increment value
        VersioningTest.objects.update(test=False)
        
        # Test value incremented correctly
        obj = VersioningTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 2)
        
        self.assertNumQueries(3)
    
    def test_queryset_update_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``update``
        method on a model queryset is called.
        """
        
        obj = VersioningTest.objects.create()
        
        # Test default value set correctly
        self.assertEquals(obj.version, 1)
        
        # Increment value
        VersioningTest.objects.all().update(test=False)
        
        # Test value incremented correctly
        obj = VersioningTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 2)
        
        self.assertNumQueries(3)


class StaticTestCase(TestCase):
    """
    Tests the behaviour of the ``StaticAbstract`` abstract model.
    
    Cover tests of parent models (see ``CommonInfoTestCase``,
    ``ArchivableTestCase``, ``VersioningTestCase``) in less detail, while still
    ensuring functionality inherits correctly.
    
    Designed to be inherited by ``TestCases`` for ``StaticAbstract`` subclasses,
    so they automatically cover common functionality, by simply overriding the
    ``setUp`` and ``get_object`` methods.
    
    Tests from "parent" ``TestCases`` not covered:
     - CommonInfoTestCase.test_object_create_with_date_created
     - CommonInfoTestCase.test_object_create_with_user_created
    """
    
    def setUp(self):
        
        self.user1 = make_user('test')
        self.user2 = make_user('test2')
    
    def get_object(self, **kwargs):
        """
        Return a StaticTest created with defaults for all required fields,
        allowing per-test saving, updating, etc without worrying about filling
        all details.
        """
        
        return StaticTest(**kwargs)
    
    def test_object_save(self):
        """
        Test object creation and modification.
        
        Covers:
         - CommonInfoTestCase.test_object_create__user
         - CommonInfoTestCase.test_object_update__user
         - VersioningTestCase.test_save_version_increment
        """
        
        obj = self.get_object()
        obj.save(self.user1)
        
        # Test object created with correct user_created and user_modified,
        # and with the correct initial version
        obj = StaticTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.user_created_id, self.user1.pk)
        self.assertEquals(obj.user_created_id, obj.user_modified_id)
        self.assertEquals(obj.version, 1)
        
        obj.save(self.user2)
        
        # Test saving the object updates the user_modified and increments the
        # version
        obj = StaticTest.objects.get(pk=obj.pk)
        self.assertEquals(obj.user_created_id, self.user1.pk)
        self.assertEquals(obj.user_modified_id, self.user2.pk)
        self.assertEquals(obj.version, 2)
        
        self.assertNumQueries(4)
    
    def test_owned_by(self):
        """
        Test object ownership checking.
        
        Covers:
         - CommonInfoTestCase.test_object_owned_by
         - CommonInfoTestCase.test_manager_owned_by
         - CommonInfoTestCase.test_queryset_owned_by
        """
        
        obj = self.get_object()
        obj.save(self.user1)
        
        # Test the object's owned_by method
        self.assertTrue(obj.owned_by(self.user1))
        self.assertFalse(obj.owned_by(self.user2))
        
        # Test the manager's owned_by method
        self.assertEquals(StaticTest.objects.owned_by(self.user1).count(), 1)
        
        # Test the queryset's owned_by method
        self.assertEquals(StaticTest.objects.all().owned_by(self.user1).count(), 1)
        
        self.assertNumQueries(3)
    
    def test_object_archive(self):
        """
        Test the extra ``live`` and ``archived`` Managers, and the
        ``archive`` and ``unarchive`` methods of the model.
        
        In addition to confirming the methods correctly set and save the
        ``is_archived`` flag, test that they correctly update the
        ``user_modified`` field in the process.
        
        Covers:
         - ArchivableTestCase.test_managers_archived_flag
         - ArchivableTestCase.test_object_archive__no_args
         - ArchivableTestCase.test_object_archive__args
         - ArchivableTestCase.test_object_unarchive__no_args
         - ArchivableTestCase.test_object_unarchive__args
        """
        
        model = StaticTest
        
        obj = self.get_object(is_archived=False)
        obj.save(self.user1)
        
        self.assertEquals(model.objects.count(), 1)
        self.assertEquals(model.live.count(), 1)
        self.assertEquals(model.archived.count(), 0)
        
        self.assertEquals(model.objects.filter(user_modified=self.user1).count(), 1)
        
        obj.archive(self.user2)
        
        self.assertEquals(model.objects.count(), 1)
        self.assertEquals(model.live.count(), 0)
        self.assertEquals(model.archived.count(), 1)
        
        self.assertEquals(model.objects.filter(user_modified=self.user2).count(), 1)
        
        obj.unarchive(self.user1)
        
        self.assertEquals(model.objects.count(), 1)
        self.assertEquals(model.live.count(), 1)
        self.assertEquals(model.archived.count(), 0)
        
        self.assertEquals(model.objects.filter(user_modified=self.user1).count(), 1)
        
        self.assertNumQueries(15)
    
    def test_queryset_archive(self):
        """
        Test the extra ``live`` and ``archived`` Managers, and the ``archive``
        and ``unarchive`` methods of the custom QuerySet used by the model's
        custom Managers.
        
        In addition to confirming the methods correctly set and save the
        ``is_archived`` flag, test that they correctly update the
        ``user_modified`` field in the process.
        
        Covers:
         - ArchivableTestCase.test_managers_archived_flag
         - ArchivableTestCase.test_queryset_archive
         - ArchivableTestCase.test_queryset_unarchive
        """
        
        model = StaticTest
        
        self.get_object(is_archived=True).save(self.user1)
        self.get_object(is_archived=False).save(self.user1)
        
        self.assertEquals(model.objects.count(), 2)
        self.assertEquals(model.live.count(), 1)
        self.assertEquals(model.archived.count(), 1)
        
        model.objects.all().archive(self.user2)
        
        self.assertEquals(model.objects.count(), 2)
        self.assertEquals(model.live.count(), 0)
        self.assertEquals(model.archived.count(), 2)
        
        model.objects.all().unarchive(self.user1)
        
        self.assertEquals(model.objects.count(), 2)
        self.assertEquals(model.live.count(), 2)
        self.assertEquals(model.archived.count(), 0)
        
        self.assertNumQueries(11)
    
    def test_manager_archive(self):
        """
        Test that the custom manager does not provide direct access to the
        custom ``archive`` and ``unarchive`` method defined on the custom
        queryset the manager is based on.
        
        Covers:
         - ArchivableTestCase.test_manager_archive_access
         - ArchivableTestCase.test_manager_unarchive_access
        """
        
        with self.assertRaises(AttributeError):
            ArchivableTest.objects.archive()
        
        with self.assertRaises(AttributeError):
            ArchivableTest.objects.unarchive()
        
        self.assertNumQueries(0)
    
    def test_update(self):
        """
        Test object modification via the QuerySet ``update`` method.
        
        Covers:
         - CommonInfoTestCase.test_manager_update
         - CommonInfoTestCase.test_queryset_update__user
         - VersioningTestCase.test_manager_update_version_increment
         - VersioningTestCase.test_queryset_update_version_increment
        """
        
        model = StaticTest
        
        obj = self.get_object()
        obj.save(self.user1)
        
        obj = model.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 1)
        self.assertEquals(obj.user_modified_id, self.user1.pk)
        
        # Test manager update method
        model.objects.update(self.user2)
        
        obj = model.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 2)
        self.assertEquals(obj.user_modified_id, self.user2.pk)
        
        # Test queryset update method
        model.objects.all().update(self.user1)
        
        obj = model.objects.get(pk=obj.pk)
        self.assertEquals(obj.version, 3)
        self.assertEquals(obj.user_modified_id, self.user1.pk)
        
        self.assertNumQueries(6)
    
    def test_object_permissions__change(self):
        """
        Test object-level "change" permission checking.
        """
        
        user1 = self.user1
        user2 = self.user2
        
        # Add model-level permission to ensure it is object-level permissions
        # being granted/denied
        permission = Permission.objects.get(codename='change_statictest')
        user1.user_permissions.add(permission)
        user2.user_permissions.add(permission)
        
        obj = self.get_object()
        obj.save(user1)
        
        # user1 should have access as it is the owner, even though "test" is
        # False. user2 should not. See StaticTest._user_can_change_statictest.
        obj.test = False
        obj.save(user1)
        self.assertTrue(user1.has_perm('app.change_statictest', obj))
        self.assertFalse(user2.has_perm('app.change_statictest', obj))
        
        # user2 should get access when "test" is True, even though it is not
        # the owner. See StaticTest._user_can_change_statictest.
        obj.test = True
        obj.save(user1)
        
        user2 = get_user_model().objects.get(pk=user2.pk)
        self.assertTrue(user2.has_perm('app.change_statictest', obj))
    
    def test_object_permissions__delete(self):
        """
        Test object-level "delete" permission checking. Also test the group
        permission side of things.
        """
        
        user1 = self.user1
        user2 = self.user2
        
        # Add model-level permission to ensure it is object-level permissions
        # being granted/denied
        permission = Permission.objects.get(codename='delete_statictest')
        user1.user_permissions.add(permission)
        user2.user_permissions.add(permission)
        
        group = Group.objects.create(name='Test Group')
        user2.groups.add(group)
        
        obj = self.get_object()
        obj.save(user1)
        
        # user1 should have access as it is the owner, regardless of group
        # permissions (from the default CommonInfoMixin ownership permissions).
        # user2 should get access because of group permissions, even though it
        # is not the owner. See StaticTest._group_can_delete_statictest.
        obj.save(user1)
        self.assertTrue(user1.has_perm('app.delete_statictest', obj))
        self.assertTrue(user2.has_perm('app.delete_statictest', obj))
        
        # user2 should lose access when "test" is False, even though they have
        # groups. See StaticTest._group_can_delete_statictest.
        obj.test = False
        obj.save(user1)
        
        user2 = get_user_model().objects.get(pk=user2.pk)
        self.assertFalse(user2.has_perm('app.delete_statictest', obj))


class TimeZoneFieldTest(TestCase):
    
    def test_init(self):
        
        f = TimeZoneField()
        
        self.assertEquals(f.choices, f.CHOICES)
        self.assertEquals(f.max_length, f.MAX_LENGTH)
    
    def test_init__custom_kwargs(self):
        
        choices = (
            ('Australia/Sydney', 'Australia/Sydney'),
            ('Australia/Melbourne', 'Australia/Melbourne'),
            ('Australia/Hobart', 'Australia/Hobart'),
            ('Australia/Adelaide', 'Australia/Adelaide'),
            ('Australia/Perth', 'Australia/Perth'),
            ('Australia/Darwin', 'Australia/Darwin'),
            ('Australia/Brisbane', 'Australia/Brisbane')
        )
        
        f = TimeZoneField(choices=choices, max_length=32)
        
        self.assertEquals(f.choices, choices)
        self.assertEquals(f.max_length, 32)
    
    def test_default(self):
        
        o = TimeZoneTest()
        
        self.assertIsInstance(o.timezone2, TimeZoneHelper)
        self.assertEquals(o.timezone2.tz.zone, 'Australia/Sydney')
    
    def test_left_null(self):
        
        o = TimeZoneTest()
        
        self.assertIsNone(o.timezone3)
    
    def test_set__string(self):
        
        o = TimeZoneTest()
        
        o.timezone = 'Australia/Sydney'
        
        # Not becoming a TimeZoneHelper until read back from the database is
        # consistent with the behaviour of fields like IntegerField,
        # DecimalField, etc
        self.assertEquals(o.timezone, 'Australia/Sydney')
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertEquals(o.timezone.tz.zone, 'Australia/Sydney')
    
    def test_set__UTC(self):
        
        o = TimeZoneTest()
        
        o.timezone = pytz.UTC
        
        # Not becoming a TimeZoneHelper until read back from the database is
        # consistent with the behaviour of fields like IntegerField,
        # DecimalField, etc
        self.assertIs(o.timezone, pytz.UTC)
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertIs(o.timezone.tz.zone, 'UTC')
    
    def test_set__timezone(self):
        
        o = TimeZoneTest()
        
        tz = pytz.timezone('Australia/Sydney')
        
        o.timezone = tz
        
        # Not becoming a TimeZoneHelper until read back from the database is
        # consistent with the behaviour of fields like IntegerField,
        # DecimalField, etc
        self.assertIs(o.timezone, tz)
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertEquals(o.timezone.tz.zone, 'Australia/Sydney')
    
    def test_set__helper(self):
        
        o = TimeZoneTest()
        
        tz = TimeZoneHelper('Australia/Sydney')
        
        o.timezone = tz
        
        self.assertIs(o.timezone, tz)
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertEquals(o.timezone.tz.zone, 'Australia/Sydney')
    
    def test_set__None(self):
        
        o = TimeZoneTest()
        
        o.timezone = pytz.UTC  # required field
        o.timezone3 = pytz.UTC
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertIs(o.timezone.tz, pytz.UTC)
        
        o.timezone3 = None
        o.save()
        
        self.assertIsNone(o.timezone3)
        
        o.refresh_from_db()
        
        self.assertIsNone(o.timezone3)
    
    def test_set__empty_string(self):
        
        o = TimeZoneTest()
        
        o.timezone = pytz.UTC  # required field
        o.timezone3 = pytz.UTC
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertIs(o.timezone.tz, pytz.UTC)
        
        o.timezone3 = ''
        o.save()
        
        self.assertEquals(o.timezone3, '')
        
        o.refresh_from_db()
        
        self.assertIsNone(o.timezone3)
    
    def test_filter(self):
        
        TimeZoneTest(timezone='Australia/Sydney').save()
        TimeZoneTest(timezone='US/Eastern').save()
        
        queryset = TimeZoneTest.objects.all()
        self.assertEquals(queryset.count(), 2)
        
        queryset = queryset.filter(timezone='Australia/Sydney')
        self.assertEquals(queryset.count(), 1)
