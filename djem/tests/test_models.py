import datetime
import pytz

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from djem.models import TimeZoneField
from djem.utils.dt import TimeZoneHelper

from .models import ArchivableTest, CommonInfoTest, StaticTest, TimeZoneTest, VersioningTest


def make_user(username):
    
    return get_user_model().objects.create_user(username, 'fakepassword')


class CommonInfoTestCase(TestCase):
    """
    Tests the behaviour of the ``CommonInfoMixin`` class, when mixed into a
    model.
    """
    
    #
    # These tests use the class-level "model" attribute so they can be applied
    # to other models (such as StaticTest) in subclasses, in order to test the
    # CommonInfoMixin's behaviour when mixed in with others (Archivable, Versioning).
    #
    
    model = CommonInfoTest
    
    def setUp(self):
        
        self.user1 = make_user('test')
        self.user2 = make_user('test2')
    
    def test_object_save__no_user__required(self):
        """
        Test the overridden ``save`` method correctly raises TypeError when
        the ``user`` argument is not provided and it is required (per
        ``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE`` setting).
        """
        
        obj = self.model()
        
        with self.assertRaises(TypeError):
            obj.save()
    
    def test_object_save__no_user__not_required(self):
        """
        Test the overridden ``save`` method correctly accepts a null ``user``
        argument when it is not required (per``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE``
        setting). Instance creation should fail on missing fields as they are
        not automatically populated by the given user.
        """
        
        obj = self.model()
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            with self.assertRaises(IntegrityError):
                obj.save()
    
    def test_object_create__user__required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when creating a new instance, passing the ``user`` argument
        when it is required.
        """
        
        obj = self.model()
        
        with self.assertNumQueries(1):
            obj.save(self.user1)
        
        # Test the object attributes are updated
        self.assertEqual(obj.user_created_id, self.user1.pk)
        self.assertEqual(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEqual(obj.date_created, obj.date_modified)
        
        # Test the changes are correctly written to the database
        obj.refresh_from_db()
        
        self.assertEqual(obj.user_created_id, self.user1.pk)
        self.assertEqual(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEqual(obj.date_created, obj.date_modified)
    
    def test_object_create__user__not_required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when creating a new instance, passing the ``user`` argument
        when it is not required. This should be identical to passing it when
        it is required.
        """
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            self.test_object_create__user__required()
    
    def test_object_create__no_user(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when creating a new instance, not using the ``user`` argument.
        """
        
        user = self.user1
        obj = self.model(user_created=user, user_modified=user)
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            with self.assertNumQueries(1):
                obj.save()
        
        # Test the object attributes are updated/not updated as necessary
        self.assertEqual(obj.user_created_id, user.pk)
        self.assertEqual(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEqual(obj.date_created, obj.date_modified)
        
        # Test the changes are correctly written to the database
        obj.refresh_from_db()
        
        self.assertEqual(obj.user_created_id, user.pk)
        self.assertEqual(obj.user_created_id, obj.user_modified_id)
        
        self.assertIsNotNone(obj.date_created)
        self.assertEqual(obj.date_created, obj.date_modified)
    
    def test_object_create__existing_date_created(self):
        """
        Test the overridden ``save`` method maintains a ``date_created`` value if
        one already exists when creating a new instance.
        """
        
        d = timezone.now() - datetime.timedelta(days=5)
        
        obj = self.model(date_created=d)
        
        with self.assertNumQueries(1):
            obj.save(self.user1)
        
        # Test the object attributes are updated
        self.assertEqual(obj.date_created, d)
        
        # Test the changes are correctly written to the database
        obj.refresh_from_db()
        self.assertEqual(obj.date_created, d)
    
    def test_object_create__existing_user_created(self):
        """
        Test the overridden ``save`` method maintains a ``user_created`` value if
        one already exists when creating a new instance.
        """
        
        obj = self.model(user_created=self.user2)
        
        with self.assertNumQueries(1):
            obj.save(self.user1)
        
        # Test the object attributes are updated
        self.assertEqual(obj.user_created_id, self.user2.pk)
        self.assertEqual(obj.user_modified_id, self.user1.pk)
        
        # Test the changes are correctly written to the database
        obj.refresh_from_db()
        self.assertEqual(obj.user_created_id, self.user2.pk)
        self.assertEqual(obj.user_modified_id, self.user1.pk)
    
    def test_object_update__user__required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when updating an existing instance, passing the ``user`` argument
        when it is required.
        """
        
        obj1 = self.model()
        obj1.save(self.user1)
        
        self.assertEqual(obj1.user_created_id, self.user1.pk)
        self.assertEqual(obj1.user_modified_id, self.user1.pk)
        self.assertTrue(obj1.field1)
        self.assertTrue(obj1.field2)
        
        # Modify some fields on a separate instance of the same record. The
        # user_modified should be saved, the date modified should be updated,
        # "field1" should be saved (listed in update_fields), "field2" should
        # NOT be saved (not listed in update_fields)
        obj2 = self.model.objects.get(pk=obj1.pk)
        obj2.field1 = False
        obj2.field2 = False
        
        with self.assertNumQueries(1):
            obj2.save(self.user2, update_fields=('field1',))
        
        # Test the object attributes are updated
        self.assertEqual(obj2.user_created_id, self.user1.pk)
        self.assertEqual(obj2.user_modified_id, self.user2.pk)
        self.assertFalse(obj2.field1)
        self.assertFalse(obj2.field2)
        
        self.assertEqual(obj2.date_created, obj1.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
        
        # Test the changes are correctly written to the database
        obj2.refresh_from_db()
        
        self.assertEqual(obj2.user_created_id, self.user1.pk)
        self.assertEqual(obj2.user_modified_id, self.user2.pk)
        self.assertFalse(obj2.field1)
        self.assertTrue(obj2.field2)
        
        self.assertEqual(obj2.date_created, obj1.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
    
    def test_object_update__user__not_required(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when updating an existing instance, passing the ``user`` argument
        when it is not required. This should be identical to passing it when
        it is required.
        """
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            self.test_object_update__user__required()
    
    def test_object_update__no_user(self):
        """
        Test the overridden ``save`` method automatically sets the necessary
        fields when updating an existing instance, not passing the ``user``
        argument.
        """
        
        user = self.user1
        
        obj1 = self.model()
        obj1.save(user)
        
        self.assertEqual(obj1.user_created_id, self.user1.pk)
        self.assertEqual(obj1.user_modified_id, self.user1.pk)
        self.assertTrue(obj1.field1)
        self.assertTrue(obj1.field2)
        
        obj2 = self.model.objects.get(pk=obj1.pk)
        obj2.field1 = False
        obj2.field2 = False
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            with self.assertNumQueries(1):
                obj2.save(update_fields=('field1',))
        
        # Test the object attributes are updated/not updated as necessary
        self.assertEqual(obj2.user_created_id, user.pk)
        self.assertEqual(obj2.user_modified_id, user.pk)
        self.assertFalse(obj2.field1)
        self.assertFalse(obj2.field2)
        
        self.assertEqual(obj2.date_created, obj1.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
        
        # Test the changes are correctly written to the database
        obj2.refresh_from_db()
        
        self.assertEqual(obj2.user_created_id, user.pk)
        self.assertEqual(obj2.user_modified_id, user.pk)
        self.assertFalse(obj2.field1)
        self.assertTrue(obj2.field2)
        
        self.assertEqual(obj2.date_created, obj1.date_created)
        self.assertGreater(obj2.date_modified, obj1.date_modified)
    
    def test_queryset_update__user__required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        passing the ``user`` argument when it is required.
        """
        
        obj = self.model()
        obj.save(self.user1)
        date_modified = obj.date_modified
        
        self.assertEqual(self.model.objects.filter(user_modified=self.user1).count(), 1)
        
        with self.assertNumQueries(1):
            self.model.objects.all().update(self.user2, field1=False)
        
        self.assertEqual(self.model.objects.filter(user_modified=self.user2).count(), 1)
        self.assertGreater(self.model.objects.first().date_modified, date_modified)
    
    def test_queryset_update__user__not_required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        passing the ``user`` argument when it is not required. This should be
        identical to passing it when it is required.
        """
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            self.test_queryset_update__user__required()
    
    def test_queryset_update__no_user__required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        not passing the ``user`` argument when it is required.
        """
        
        obj = self.model()
        obj.save(self.user1)
        
        with self.assertNumQueries(0):
            with self.assertRaises(TypeError):
                self.model.objects.all().update(field1=False)
    
    def test_queryset_update__no_user__not_required(self):
        """
        Test the overridden ``update`` method of the custom queryset
        automatically sets the necessary fields when updating existing records,
        not passing the ``user`` argument when it is not required.
        """
        
        user = self.user1
        
        obj = self.model()
        obj.save(user)
        date_modified = obj.date_modified
        
        self.assertEqual(self.model.objects.filter(user_modified=user).count(), 1)
        
        with self.settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False):
            with self.assertNumQueries(1):
                self.model.objects.all().update(field1=False)
        
        self.assertEqual(self.model.objects.filter(user_modified=user).count(), 1)
        self.assertGreater(self.model.objects.first().date_modified, date_modified)
    
    def test_manager_update(self):
        """
        Test the overridden ``update`` method of the custom queryset, accessed
        from the custom manager.
        """
        
        obj = self.model()
        obj.save(self.user1)
        date_modified = obj.date_modified
        
        self.assertEqual(self.model.objects.filter(user_modified=self.user1).count(), 1)
        
        with self.assertNumQueries(1):
            self.model.objects.update(self.user2, field1=False)
        
        self.assertEqual(self.model.objects.filter(user_modified=self.user2).count(), 1)
        self.assertGreater(self.model.objects.first().date_modified, date_modified)
    
    def test_object_owned_by(self):
        """
        Test the ``owned_by`` method of a model instance.
        """
        
        obj1 = self.model()
        obj1.save(self.user1)
        
        obj2 = self.model()
        obj2.save(self.user2)
        
        with self.assertNumQueries(0):
            self.assertTrue(obj1.owned_by(self.user1))
            self.assertTrue(obj1.owned_by(self.user1.pk))
            self.assertFalse(obj1.owned_by(self.user2))
            
            self.assertTrue(obj2.owned_by(self.user2))
            self.assertTrue(obj2.owned_by(self.user2.pk))
            self.assertFalse(obj2.owned_by(self.user1))
    
    def test_queryset_owned_by(self):
        """
        Test the ``owned_by`` method of the custom queryset.
        """
        
        self.model().save(self.user1)
        self.model().save(self.user2)
        
        self.assertEqual(self.model.objects.count(), 2)
        
        qs = self.model.objects.all()
        
        with self.assertNumQueries(1):
            self.assertEqual(qs.owned_by(self.user1).count(), 1)
        
        with self.assertNumQueries(1):
            self.assertEqual(qs.owned_by(self.user1.pk).count(), 1)
        
        with self.assertNumQueries(1):
            self.assertEqual(qs.filter(field1=False).owned_by(self.user1).count(), 0)
        
        with self.assertNumQueries(1):
            self.assertEqual(qs.owned_by(self.user1).owned_by(self.user2).count(), 0)
    
    def test_manager_owned_by(self):
        """
        Test the ``owned_by`` method of the custom queryset, accessed from the
        manager.
        """
        
        self.model().save(self.user1)
        self.model().save(self.user2)
        
        self.assertEqual(self.model.objects.count(), 2)
        
        # Test owned_by with user object
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.owned_by(self.user1).count(), 1)
        
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.owned_by(self.user2).count(), 1)
        
        # Test owned_by with user id
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.owned_by(self.user1.pk).count(), 1)
        
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.owned_by(self.user2.pk).count(), 1)


class ArchivableTestCase(TestCase):
    """
    Tests the behaviour of the ``ArchivableMixin`` class, when mixed into a
    model.
    """
    
    #
    # These tests use the class-level "model" attribute and the create_instance()
    # method so they can be applied to other models (such as StaticTest) in
    # subclasses, in order to test the ArchivableMixin's behaviour when mixed
    # in with others (CommonInfo, Versioning).
    # The tests are decorated so they don't raise an exception when calling the
    # save() method without a user argument if they are called on a model that
    # is mixed into CommonInfoMixin.
    #
    
    model = ArchivableTest
    
    def create_instance(self, **kwargs):
        
        return self.model.objects.create(**kwargs)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_object_archive__no_args(self):
        """
        Test the ``archive()`` method of an instance, when called with no
        arguments.
        """
        
        obj = self.create_instance(is_archived=False)
        
        self.assertFalse(obj.is_archived)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
        
        # Change the fields and archive the record - the changes to the fields
        # should not be saved
        with self.assertNumQueries(1):
            obj.field1 = False
            obj.field2 = False
            obj.archive()
        
        obj.refresh_from_db()
        self.assertTrue(obj.is_archived)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_object_archive__args(self):
        """
        Test the ``archive()`` method of an instance, when called with the
        ``update_fields`` argument. It should pass the argument through to its
        internal call to ``save()``.
        """
        
        obj = self.create_instance(is_archived=False)
        
        self.assertFalse(obj.is_archived)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
        
        # Change the fields and archive the record - only the to "field1" should
        # be saved
        with self.assertNumQueries(1):
            obj.field1 = False
            obj.field2 = False
            obj.archive(update_fields=('field1',))
        
        obj.refresh_from_db()
        self.assertTrue(obj.is_archived)
        self.assertFalse(obj.field1)
        self.assertTrue(obj.field2)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_object_unarchive__no_args(self):
        """
        Test the ``unarchive()`` method of an instance, when called with no
        arguments.
        """
        
        obj = self.create_instance(is_archived=True)
        
        self.assertTrue(obj.is_archived)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
        
        # Change the fields and archive the record - the changes to the fields
        # should not be saved
        with self.assertNumQueries(1):
            obj.field1 = False
            obj.field2 = False
            obj.unarchive()
        
        obj.refresh_from_db()
        self.assertFalse(obj.is_archived)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_object_unarchive__args(self):
        """
        Test the ``unarchive()`` method of an instance, when called with the
        ``update_fields`` argument. It should pass the argument through to its
        internal call to ``save()``.
        """
        
        obj = self.create_instance(is_archived=True)
        
        self.assertTrue(obj.is_archived)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
        
        # Change the fields and archive the record - only the to "field1" should
        # be saved
        with self.assertNumQueries(1):
            obj.field1 = False
            obj.field2 = False
            obj.unarchive(update_fields=('field1',))
        
        obj.refresh_from_db()
        self.assertFalse(obj.is_archived)
        self.assertFalse(obj.field1)
        self.assertTrue(obj.field2)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_queryset_archived(self):
        """
        Test the custom queryset ``archived()`` method correctly filters to
        archived records, both when called directly from the manager and when
        called on the queryset.
        """
        
        self.create_instance(is_archived=True, field1=True)
        self.create_instance(is_archived=True, field1=True)
        self.create_instance(is_archived=True, field1=False)
        
        self.create_instance(is_archived=False, field1=True)
        self.create_instance(is_archived=False, field1=False)
        
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.archived().count(), 3)
        
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.filter(field1=True).archived().count(), 2)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_queryset_unarchive(self):
        """
        Test the custom queryset ``unarchived()`` method correctly filters to
        non-archived records, both when called directly from the manager and
        when called on the queryset.
        """
        
        self.create_instance(is_archived=True, field1=True)
        self.create_instance(is_archived=True, field1=False)
        
        self.create_instance(is_archived=False, field1=True)
        self.create_instance(is_archived=False, field1=True)
        self.create_instance(is_archived=False, field1=False)
        
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.unarchived().count(), 3)
        
        with self.assertNumQueries(1):
            self.assertEqual(self.model.objects.filter(field1=True).unarchived().count(), 2)


class VersioningTestCase(TestCase):
    """
    Tests the behaviour of the ``VersioningMixin`` class, when mixed into a
    model.
    """
    
    #
    # These tests use the class-level "model" attribute and the create_instance()
    # method so they can be applied to other models (such as StaticTest) in
    # subclasses, in order to test the VersioningMixin's behaviour when mixed
    # in with others (CommonInfo, Archivable).
    # The tests are decorated so they don't raise an exception when calling the
    # save() method without a user argument if they are called on a model that
    # is mixed into CommonInfoMixin.
    #
    
    model = VersioningTest
    
    def create_instance(self, **kwargs):
        
        return self.model.objects.create(**kwargs)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_save_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``save``
        method on a model instance is called.
        """
        
        obj = self.create_instance()
        
        # Test default value set correctly on object
        self.assertEqual(obj.version, 1)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
        
        # Test default value correctly saved to the database without increment
        obj.refresh_from_db()
        self.assertEqual(obj.version, 1)
        self.assertTrue(obj.field1)
        self.assertTrue(obj.field2)
        
        # Make a change and test it was saved correctly
        with self.assertNumQueries(1):
            obj.field1 = False
            obj.field2 = False
            obj.save(update_fields=('field1',))
        
        obj.refresh_from_db()
        self.assertEqual(obj.version, 2)  # should be incremented
        self.assertFalse(obj.field1)      # should be modified
        self.assertTrue(obj.field2)       # should not be modified (not listed in update_fields)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_multiple_save_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``save``
        method on a model instance is called multiple times.
        """
        
        obj = self.create_instance()  # version 1
        
        with self.assertNumQueries(1):
            obj.save()  # version 2
        
        with self.assertNumQueries(1):
            obj.save()  # version 3
        
        # Test incremented value correctly saved to the database
        obj.refresh_from_db()
        self.assertEqual(obj.version, 3)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_version_inaccessible_after_increment(self):
        """
        Test the version field is no longer accessible after it has been
        atomically incremented.
        """
        
        obj = self.create_instance()
        
        # Increment value
        with self.assertNumQueries(1):
            obj.save()
        
        # New version cannot be known on the same instance - it has to be
        # requeried
        with self.assertRaises(self.model.AmbiguousVersionError):
            bool(obj.version)  # bool() used purely to force evaluation of SimpleLazyObject
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_manager_update_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``update``
        method on a model manager is called.
        """
        
        obj = self.create_instance()
        
        # Test default value set correctly
        self.assertEqual(obj.version, 1)
        
        # Increment value
        with self.assertNumQueries(1):
            self.model.objects.update(field1=False)
        
        # Test value incremented correctly
        obj.refresh_from_db()
        self.assertEqual(obj.version, 2)
    
    @override_settings(DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
    def test_queryset_update_version_increment(self):
        """
        Test the version field is correctly auto-incremented when the ``update``
        method on a model queryset is called.
        """
        
        obj = self.create_instance()
        
        # Test default value set correctly
        self.assertEqual(obj.version, 1)
        
        # Increment value
        with self.assertNumQueries(1):
            self.model.objects.all().update(field1=False)
        
        # Test value incremented correctly
        obj.refresh_from_db()
        self.assertEqual(obj.version, 2)


class StaticTestCase(CommonInfoTestCase, ArchivableTestCase, VersioningTestCase):
    
    model = StaticTest
    
    def create_instance(self, **kwargs):
        
        # Automatically add the required user created/modified values, to
        # enable the tests inherited from ArchivableTestCase and VersioningTestCase
        kwargs['user_created'] = self.user1
        kwargs['user_modified'] = self.user1
        
        obj = self.model(**kwargs)
        obj.save()
        
        return obj


class TimeZoneFieldTest(TestCase):
    
    def test_init(self):
        
        f = TimeZoneField()
        
        self.assertEqual(f.choices, f.CHOICES)
        self.assertEqual(f.max_length, f.MAX_LENGTH)
    
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
        
        self.assertEqual(f.choices, choices)
        self.assertEqual(f.max_length, 32)
    
    def test_default(self):
        
        o = TimeZoneTest()
        
        self.assertIsInstance(o.timezone2, TimeZoneHelper)
        self.assertEqual(o.timezone2.tz.zone, 'Australia/Sydney')
    
    def test_set__string(self):
        
        o = TimeZoneTest()
        
        o.timezone = 'Australia/Sydney'
        
        # Not becoming a TimeZoneHelper until read back from the database is
        # consistent with the behaviour of fields like IntegerField,
        # DecimalField, etc
        self.assertEqual(o.timezone, 'Australia/Sydney')
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertEqual(o.timezone.tz.zone, 'Australia/Sydney')
    
    def test_set__string__invalid_timezone(self):
        
        o = TimeZoneTest()
        
        o.timezone = 'fail'
        
        # Not being validated until the model instance is saved is consistent
        # with the behaviour of fields like IntegerField, DecimalField, etc
        self.assertEqual(o.timezone, 'fail')
        
        with self.assertRaisesRegex(ValidationError, 'Invalid timezone "fail"'):
            o.save()
    
    def test_set__string__invalid_timezone__in_choices(self):
        
        o = TimeZoneTest()
        
        o.timezone = 'invalid'
        
        # Not being validated until the model instance is saved is consistent
        # with the behaviour of fields like IntegerField, DecimalField, etc
        self.assertEqual(o.timezone, 'invalid')
        
        with self.assertRaisesRegex(ValidationError, 'Invalid timezone "invalid"'):
            o.save()
    
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
        self.assertEqual(o.timezone.tz.zone, 'Australia/Sydney')
    
    def test_set__helper(self):
        
        o = TimeZoneTest()
        
        tz = TimeZoneHelper('Australia/Sydney')
        
        o.timezone = tz
        
        self.assertIs(o.timezone, tz)
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertEqual(o.timezone.tz.zone, 'Australia/Sydney')
    
    def test_set__None__null_true(self):
        
        o = TimeZoneTest()
        
        o.timezone3 = pytz.UTC
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone3, TimeZoneHelper)
        self.assertIs(o.timezone3.tz, pytz.UTC)
        
        o.timezone3 = None
        o.save()
        
        # The field's python value will be None and it will be stored in the
        # database as a null
        self.assertIsNone(o.timezone3)
        
        o.refresh_from_db()
        self.assertIsNone(o.timezone3)
        
        self.assertEqual(TimeZoneTest.objects.count(), 1)
        self.assertEqual(TimeZoneTest.objects.filter(timezone3__isnull=True).count(), 1)
    
    def test_set__None__null_false(self):
        
        o = TimeZoneTest()
        
        o.timezone = pytz.UTC
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertIs(o.timezone.tz, pytz.UTC)
        
        o.timezone = None
        o.save()
        
        # The field's python value will be None (as opposed to a TimeZoneHelper
        # with a timezone of the empty string), but it will be stored in the
        # database as an empty string
        self.assertIsNone(o.timezone)
        
        o.refresh_from_db()
        self.assertIsNone(o.timezone)
        
        self.assertEqual(TimeZoneTest.objects.count(), 1)
        self.assertEqual(TimeZoneTest.objects.filter(timezone__isnull=True).count(), 0)
        self.assertEqual(TimeZoneTest.objects.filter(timezone='').count(), 1)
    
    def test_set__empty_string__null_true(self):
        
        o = TimeZoneTest()
        
        o.timezone3 = pytz.UTC
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone3, TimeZoneHelper)
        self.assertIs(o.timezone3.tz, pytz.UTC)
        
        o.timezone3 = ''
        o.save()
        
        # The field's python value will revert to None after being read back
        # from the database (as opposed to a TimeZoneHelper with a timezone of
        # the empty string) and it will be stored in the database as a null
        self.assertEqual(o.timezone3, '')
        
        o.refresh_from_db()
        self.assertIsNone(o.timezone3)
        
        self.assertEqual(TimeZoneTest.objects.count(), 1)
        self.assertEqual(TimeZoneTest.objects.filter(timezone3__isnull=True).count(), 1)
    
    def test_set__empty_string__null_false(self):
        
        o = TimeZoneTest()
        
        o.timezone = pytz.UTC
        
        o.save()
        o.refresh_from_db()
        
        self.assertIsInstance(o.timezone, TimeZoneHelper)
        self.assertIs(o.timezone.tz, pytz.UTC)
        
        o.timezone = ''
        o.save()
        
        # The field's python value will revert to None after being read back
        # from the database (as opposed to a TimeZoneHelper with a timezone of
        # the empty string) and it will be stored in the database as an empty
        # string
        self.assertEqual(o.timezone, '')
        
        o.refresh_from_db()
        self.assertIsNone(o.timezone)
        
        self.assertEqual(TimeZoneTest.objects.count(), 1)
        self.assertEqual(TimeZoneTest.objects.filter(timezone__isnull=True).count(), 0)
        self.assertEqual(TimeZoneTest.objects.filter(timezone='').count(), 1)
    
    def test_filter(self):
        
        TimeZoneTest(timezone='Australia/Sydney').save()
        TimeZoneTest(timezone='US/Eastern').save()
        
        queryset = TimeZoneTest.objects.all()
        self.assertEqual(queryset.count(), 2)
        
        queryset = queryset.filter(timezone='Australia/Sydney')
        self.assertEqual(queryset.count(), 1)
