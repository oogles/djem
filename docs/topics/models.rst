======
Models
======

.. module:: django_goodies.models

Django Goodies provides a series of custom classes to support common model-related functionality, including models, model managers and model fields.


.. _commoninfomixin:

CommonInfoMixin
===============

The :class:`CommonInfoMixin` class is designed as a mixin for Django models, providing:

* Standard user and datetime fields: ``user_created``, ``user_modified``, ``date_created``, ``date_modified``.
* Support for :ref:`ensuring these fields remain accurate <commoninfomixin-maintaining-accuracy>` as records are updated over time.
* Support for :ref:`ownership checking <commoninfomixin-ownership-checking>`.
* A simple :ref:`default implementation <commoninfomixin-object-permissions>` of :doc:`permissions` via ownership checking.
* A custom manager to assist with maintaining accuracy and checking ownership.

.. warning::
    
    Using :class:`CommonInfoMixin` can break code that automatically calls methods such as the model's :meth:`~CommonInfoMixin.save` method, or the queryset's :meth:`~django_goodies.models.managers.CommonInfoQuerySet.update` method. See :ref:`commoninfomixin-maintaining-accuracy` for a description of the caveats of ``CommonInfoMixin``, and workarounds.

Usage
-----

To make use of :class:`CommonInfoMixin`, simply include it among your model's parent classes:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import CommonInfoMixin
    
    class ExampleModel(CommonInfoMixin, models.Model):
        
        name = models.CharField(max_length=64)

Default values
--------------

The ``date_created`` and ``date_modified`` fields will default to ``django.utils.timezone.now()`` at the moment the instance is initially saved.

The ``user_created`` and ``user_modified`` fields will require a ``User`` instance in order to populate their values. However, they do not need to be populated manually. Django Goodies provides various mechanisms to both make it easy to populate these fields automatically, and to ensure they are populated any time a record is updated. See :ref:`commoninfomixin-maintaining-accuracy`.

If any of the fields *are* populated manually, their values will not be overwritten.

.. _commoninfomixin-maintaining-accuracy:

Maintaining accuracy
--------------------

The fields provided by :class:`CommonInfoMixin` are designed to be automatically populated whenever necessary. And in the case of ``date_modified`` and ``user_modified``, it is necessary to update them whenever a record is updated.

For the date fields, this is easy to accomplish. For the user fields, it requires something extra - knowledge of the user doing the creating/updating.

Various means exist to provide this:

Calling ``save()`` on the instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`CommonInfoMixin.save` method is overridden to require a ``User`` instance as the first argument. This allows the method to populate ``user_created`` when a new instance is being created, and keep ``user_modified`` up to date as changes are made.

.. code-block:: python
    
    >>> bill = User.objects.get(username='bill')
    >>> ben = User.objects.get(username='ben')
    >>> obj = ExampleModel(name='Awesome Example')
    >>> obj.user_created
    None
    >>> obj.save(bill)
    >>> obj.user_created.username
    "bill"
    >>> obj.user_modified.username
    "bill"
    >>> obj.save(ben)
    >>> obj.user_created.username
    "bill"
    >>> obj.user_modified.username
    "ben"

.. note::
    
    These fields will be updated even if the :meth:`~CommonInfoMixin.save` method is passed a sequence of ``update_fields`` that does not include it (see `Django documentation for update_fields <https://docs.djangoproject.com/en/stable/ref/models/instances/#specifying-which-fields-to-save>`_). They will simply be appended to the list.

Calling ``update()`` on the queryset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Like :meth:`CommonInfoMixin.save`, the ``CommonInfoMixin`` queryset's :meth:`~django_goodies.models.managers.CommonInfoQuerySet.update` method is also overridden to require a ``User`` instance as the first argument. Again, this allows the method to keep ``user_modified`` up to date as changes are made.

.. code-block:: python
    
    >>> ben = User.objects.get(username='ben')
    >>> ExampleModel.objects.values_list('name', 'user_created__username', 'user_modified__username')
    [("Good Example", "bill", "bill")]
    >>> obj = ExampleModel.objects.filter(name='Good Example').update(ben, name='Great Example')
    >>> ExampleModel.objects.values_list('name', 'user_created__username', 'user_modified__username')
    [("Great Example", "bill", "ben")]

Using forms
~~~~~~~~~~~

In a Django web application, a common way that changes are made and instances are saved is via a ``ModelForm``. Django's own ``ModelForm`` class will not pass the required ``User`` argument to the model's ``save()`` method when it calls it internally. Therefore, Django Goodies provides :class:`~django_goodies.forms.CommonInfoForm`. Designed to replace ``ModelForm`` as the parent of forms for models incorporating :class:`CommonInfoMixin`, ``CommonInfoForm`` takes a ``User`` instance as a constructor argument, giving it a known user to pass to the model's ``save()`` method when the form is saved.

.. code-block:: python
    
    # forms.py
    from django_goodies.forms import CommonInfoForm
    
    class ExampleForm(CommonInfoForm):
        
        class Meta:
            model = ExampleModel
            fields = ['name']
    
    # views.py
    def create_example(request):
        #...
        form = ExampleForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
        #...

Caveats and workarounds
~~~~~~~~~~~~~~~~~~~~~~~

Obviously any code that calls a model's ``save()`` method or a queryset's ``update()`` method will need to be updated to pass the ``user`` argument for models that incorporate :class:`CommonInfoMixin`. This may not always be possible for third party code. :class:`~django_goodies.forms.CommonInfoForm` solves this problem for one common occurrence, by providing a wrapper around Django's ``ModelForm``, but there are plenty of others. E.g. the queryset methods ``create()`` and ``get_or_create()``, which are not currently supported.

If it is not feasible to customise code that calls these methods, it *is* possible to disable the "required-ness" of the ``user`` argument, by setting :ref:`setting-GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE` to ``False`` in ``settings.py``:

.. code-block:: python
    
    GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE = False

This allows the use of ``CommonInfoMixin`` and all related functionality without the strict requirement of passing the ``user`` argument to methods that save/update the record. If passed, it will still be used as usual, but not providing it will not raise an exception. Of course, the methods won't automatically populate the appropriate fields. This means that ``user_created`` and ``user_modified`` will need to be manually populated when creating, and ``user_modified`` will need to be manually populated when updating.

.. versionadded:: 0.4
    The :ref:`setting-GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE` setting
    
.. warning::
    
    Setting :ref:`setting-GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE` to ``False`` reduces the accuracy of the ``user_modified`` field, as it cannot be guaranteed that the user that made a change was recorded.

.. note::
    
    As the accuracy of the ``user_modified`` field is often irrelevant in tests, setting :ref:`setting-GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE` to ``False`` using `override_settings() <https://docs.djangoproject.com/en/stable/topics/testing/tools/#django.test.override_settings>`_ can help make updating model instances in tests a bit easier.
    
    E.g.
    
    .. code-block:: python
        
        from django.test import TestCase, override_settings
        
        # For the whole TestCase:
        
        @override_settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
        class ExampleModelTestCase(TestCase):
            # ...
        
        # For specific tests:
        
        class LoginTestCase(TestCase):
        
            @override_settings(GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE=False)
            def test_something(self):
                # ...

An additional caveat is that there may not always be a known user when a change is being made to a ``CommonInfoMixin`` record, e.g. during a system-triggered background process. Situations such as these may be solved by setting :ref:`setting-GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE` as described above, and taking responsibility for keeping ``user_modified`` up to date when necessary, or by creating a "system" user that can be passed in during these operations.


.. _commoninfomixin-ownership-checking:

Ownership checking
------------------

:class:`CommonInfoMixin` also adds support for *ownership checking*. The :meth:`~CommonInfoMixin.owned_by` method can be called on an model instance to check if the instance is owned by the given user. The user can be provided either as a ``User`` instance or as the primary key of a ``User`` record.

.. code-block:: python
    
    >>> bill = User.objects.get(username='bill')
    >>> ben = User.objects.get(username='ben')
    >>> obj = ExampleModel(name='Awesome Example')
    >>> obj.save(bill)
    >>> obj.owned_by(bill)
    True
    >>> obj.owned_by(ben)
    False

Ownership checking is also available via a ``CommonInfoMixin`` model's manager and queryset. The queryset's :meth:`~django_goodies.models.managers.CommonInfoQuerySet.owned_by` method also accepts a user as a ``User`` instance or as the primary key of a ``User`` record. It returns a queryset filtered to records where the ``user_created`` field matches the given user.

.. code-block:: python
    
    >>> ExampleModel.objects.owned_by(bill)
    [<ExampleModel: Awesome Example>]
    >>> ExampleModel.objects.owned_by(ben)
    []
    >>> ExampleModel.objects..filter(name__contains='Great').owned_by(bill)
    []


.. _commoninfomixin-object-permissions:

Object-level permissions
------------------------

.. versionadded:: 0.4

:class:`CommonInfoMixin` comes with a default, simple implementation of :doc:`permissions`, using :ref:`ownership checking <commoninfomixin-ownership-checking>`, for the default Django permissions of "change" and "delete". That is, a user will be granted object-level "change" or "delete" permissions if they are the owner of the object. If they are not the owner, they will be denied the permission.

.. code-block:: python
    
    >>> bill = User.objects.get(username='bill')
    >>> ben = User.objects.get(username='ben')
    >>> obj = ExampleModel(name='Awesome Example')
    >>> obj.save(bill)
    >>> bill.has_perm('myapp.change_examplemodel', obj)
    True
    >>> ben.has_perm('myapp.change_examplemodel', obj)
    False

.. note::
    
    As per the implementation of object-level permissions, the object-level permission check is only performed if the model-level permission has also been granted to the user in question. In the above example, the given user would need to have the "change_examplemodel" permission at the model level. Otherwise, they would fail the object-level check, even if they were the owner.


.. _archivablemixin:

ArchivableMixin
===============

The :class:`ArchivableMixin` class is designed as a mixin for Django models, providing:

* An ``is_archived`` Boolean field, defaulting to ``False``.
* :ref:`Three different managers <archivablemixin-managers>` (``objects``, ``live`` and ``archived``) for accessing data with various states of ``is_archived``.
* Support for :ref:`archiving and unarchiving <archivablemixin-archiving-unarchiving>`, both at the instance level and the queryset level.

Usage
-----

To make use of :class:`ArchivableMixin`, simply include it among your model's parent classes:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import ArchivableMixin
    
    class ExampleModel(ArchivableMixin, models.Model):
        
        name = models.CharField(max_length=64)

.. _archivablemixin-managers:

The managers
------------

:class:`ArchivableMixin` provides three managers: ``objects``, ``live`` and ``archived``.

The three differ in the default querysets they provide:

- ``objects`` provides access to all records, as per usual
- ``live`` filters to records with the ``is_archived`` flag set to ``False``
- ``archived`` filters to records with the ``is_archived`` flag set to ``True``

.. code-block:: python
    
    >>> ExampleModel(name='Example1', is_archived=True).save()
    >>> ExampleModel(name='Example2', is_archived=False).save()
    >>> ExampleModel.objects.count()
    2
    >>> ExampleModel.live.count()
    1
    >>> ExampleModel.archived.count()
    1

.. _archivablemixin-archiving-unarchiving:

Archiving and unarchiving
-------------------------

Instances of :class:`~ArchivableMixin` have the :meth:`~ArchivableMixin.archive` and :meth:`~ArchivableMixin.unarchive` methods. These set the ``is_archived`` flag of the instance to ``True`` or ``False``, respectively, and save the instance. Any arguments provided to them are passed through to their internal calls to ``save()``.

.. code-block:: python
    
    >>> obj = ExampleModel(name='Awesome Example')
    >>> obj.save()
    >>> ExampleModel.objects.get(name='Awesome Example').is_archived
    False
    >>> obj.archive()
    >>> ExampleModel.objects.get(name='Awesome Example').is_archived
    True
    >>> obj.unarchive()
    >>> ExampleModel.objects.get(name='Awesome Example').is_archived
    False

Archiving/unarchiving records in bulk is also possible via the queryset's :meth:`~django_goodies.models.managers.ArchivableQuerySet.archive` and :meth:`~django_goodies.models.managers.ArchivableQuerySet.unarchive` methods.

.. code-block:: python
    
    >>> ExampleModel(name='Example1', is_archived=True).save()
    >>> ExampleModel(name='Example2', is_archived=False).save()
    >>> print ExampleModel.live.count(), ExampleModel.archived.count()
    1, 1
    >>> ExampleModel.objects.all().archive()
    1
    >>> print ExampleModel.live.count(), ExampleModel.archived.count()
    0, 2
    >>> ExampleModel.objects.all().unarchive()
    2
    >>> print ExampleModel.live.count(), ExampleModel.archived.count()
    2, 0

.. note::
    
    The :ref:`managers <archivablemixin-managers>` do not provide access to the bulk :meth:`~django_goodies.models.managers.ArchivableQuerySet.archive` and :meth:`~django_goodies.models.managers.ArchivableQuerySet.unarchive` methods directly. Like ``delete()``, ``archive()`` and ``unarchive()`` are only accessible via a QuerySet.
    
    .. code-block:: python
        
        # invalid
        >>> ExampleModel.objects.archive()
        
        # valid
        >>> ExampleModel.objects.all().archive()


.. _versioningmixin:

VersioningMixin
===============

The :class:`VersioningMixin` class is designed as a mixin for Django models, providing a ``version`` field that is automatically incremented on every save.

Usage
-----

To make use of :class:`VersioningMixin`, simply include it among your model's parent classes:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import VersioningMixin
    
    class ExampleModel(VersioningMixin, models.Model):
        
        name = models.CharField(max_length=64)

.. _versioningmixin-incrementing-version:

Incrementing ``version``
------------------------

Incrementation of the ``version`` field is done atomically, through the use of a Django ``F()`` expression, to avoid possible race conditions. See `Django documentation for F() expressions <https://docs.djangoproject.com/en/stable/ref/models/expressions/#django.db.models.F>`_.

To ensure the ``version`` field is always kept current, :class:`VersioningMixin` overrides the :meth:`~VersioningMixin.save` method and the :meth:`~django_goodies.models.managers.VersioningQuerySet.update` method of the custom manager/queryset.

.. note::
    
    The ``version`` field will be updated even if the ``save`` method is passed a sequence of ``update_fields`` that does not include it (see `Django documentation for update_fields <https://docs.djangoproject.com/en/stable/ref/models/instances/#specifying-which-fields-to-save>`_). It will simply be appended to the list.

.. warning::
    
    Once an instance is saved and the ``F()`` expression is used to increment the version, the ``version`` field will become a Django ``Expression`` instance. At this point, it is no longer accessible as an integer. For the same reason an ``F()`` expression is used to perform the incrementation (race conditions), the new version cannot be retrieved from the database after the save and used to replace the ``Expression`` value. There is the possibility the version retrieved will not be the one that matches the rest of the values on the model. The only way to regain a usable ``version`` field after saving a model instance is requerying for the whole instance.
    Attempting to access the ``version`` field after it has been incremented will raise a :exc:`VersioningMixin.AmbiguousVersionError` exception.

.. note::
    
    Even though directly accessing the ``version`` field is not possible after it has been atomically incremented, subsequent saves of the same instance will continue to correctly increment it.


Mixing Mixins
=============

A model can include any combination of the above mixins. However, since they all use custom managers to provide additional functionality unique to them, a model using multiple mixins will need to provide its own manager that incorporates the functionality of each. For most mixins, this is only necessary for ``objects``, but for :ref:`archivablemixin`, the ``live`` and ``archived`` managers will also need to be customised.

The following is an example of a model using the :ref:`commoninfomixin` and :ref:`archivablemixin`.

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import CommonInfoMixin, ArchivableMixin
    from django_goodies.managers import (
        ArchivableManager, ArchivableQuerySet, CommonInfoManager, CommonInfoQuerySet
    )
    
    class ExampleQuerySet(CommonInfoQuerySet, ArchivableQuerySet):
        
        # Need to override the "archive" and "unarchive" methods inherited from
        # ArchivableQuerySet as they call "update", which requires a User
        # argument thanks to CommonInfoQuerySet.
        
        def archive(self, user):
            
            self.update(user, is_archived=True)
        
        def unarchive(self, user):
            
            self.update(user, is_archived=False)
    
    class ExampleManager(CommonInfoManager, ArchivableManager):
        
        def get_queryset(self):
            
            return ExampleQuerySet(self.model, using=self._db)
    
    class ExampleModel(CommonInfoMixin, ArchivableMixin, models.Model):
        
        name = models.CharField(max_length=64)
        
        objects = ExampleManager()
        live = ExampleManager(archived=False)
        archived = ExampleManager(archived=True)

For a ready-made combination of all three mixins (:ref:`commoninfomixin`, :ref:`archivablemixin` and :ref:`versioningmixin`), see :ref:`staticabstract`.


.. _staticabstract:

StaticAbstract
==============

:class:`StaticAbstract` is a combination of :ref:`commoninfomixin`, :ref:`archivablemixin` and :ref:`versioningmixin`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields, as well as custom ``objects``, ``live`` and ``archived`` managers, and provides access to all the functionality offered by each of the mixins, including:

* :ref:`Maintaining the accuracy <commoninfomixin-maintaining-accuracy>` of ``date_modified`` and ``user_modified`` as changes are made.
* Automatically and :ref:`atomically incrementing <versioningmixin-incrementing-version>` ``version`` as changes are made.
* Allowing :ref:`archiving and unarchiving <archivablemixin-archiving-unarchiving>`.
* Providing :ref:`ownership checking <commoninfomixin-ownership-checking>`.
* Providing basic :ref:`object-level permissions support <commoninfomixin-object-permissions>`.

Usage
-----

To make use of :class:`StaticAbstract`, simply inherit from it:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import StaticAbstract
    
    class ExampleModel(StaticAbstract):
        
        name = models.CharField(max_length=64)


TimeZoneField
=============

.. versionadded:: 0.3

:class:`TimeZoneField` is a model field that stores timezone name strings ('Australia/Sydney', 'US/Eastern', etc) in the database and provides access to :class:`~django_goodies.utils.dt.TimeZoneHelper` instances for the stored timezones, as :ref:`explained below <timezonefield-timezonehelper>`.

In forms, a :class:`TimeZoneField` is represented by a ``TypedChoiceField``, and rendered using a ``Select`` widget by default.

.. note::
    
    Use of :class:`TimeZoneField` requires `pytz <http://pytz.sourceforge.net/>`_ to be installed. It will raise an exception during instantiation if ``pytz`` is not available.

.. note::
    
    Use of :class:`TimeZoneField` only makes sense if `USE_TZ <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-USE_TZ>`_ is True.

Usage
-----

:class:`TimeZoneField` is used just like any model field. The following demonstrates adding a ``time_zone`` field to a custom ``User`` model.

.. code-block:: python
    
    from django.contrib.auth.models import AbstractBaseUser
    from django_goodies.models import TimeZoneField
    
    class User(AbstractBaseUser):
        ...
        time_zone = TimeZoneField()

Accessing the ``time_zone`` field on a ``User`` instance yields a :class:`~django_goodies.utils.dt.TimeZoneHelper` instance, which provides some helpers for dealing with times in local timezones, as :ref:`explained below <timezonefield-timezonehelper>`.

.. code-block:: python
    
    >>> user = User.objects.get(timezone='Australia/Sydney')
    >>> user.timezone
    <TimeZoneHelper: Australia/Sydney>

Available Timezones
-------------------

:class:`TimeZoneField` is a reasonably light wrapper around a ``CharField``, providing a default value for the ``choices`` argument. The default choices are taken from `pytz.common_timezones <http://pytz.sourceforge.net/#helpers>`_.

These choices can be modified in the same way as any other ``CharField``. However, they need to be valid timezone name strings as per the Olson tz database, `used by pytz <http://pytz.sourceforge.net/#introduction>`_.

For example, using a very limited set of timezones:

.. code-block:: python
    
    from django.contrib.auth.models import AbstractBaseUser
    from django_goodies.models import TimeZoneField
    
    class User(AbstractBaseUser):
        ...
        time_zone = TimeZoneField(choices=(
            ('Australia/Brisbane'),
            ('Australia/Sydney'),
            ('Australia/Melbourne')
        ))

.. _timezonefield-timezonehelper:

TimeZoneHelper
--------------

:class:`~django_goodies.utils.dt.TimeZoneHelper` is a simple helper class that provides shortcuts for getting the current date and the current datetime for a known local timezone.

Assuming a ``User`` model with a ``time_zone`` field, as shown above:

.. code-block:: python
    
    >>> aus_user = User.objects.get(timezone='Australia/Sydney')
    >>> aus_user.timezone.name
    'Australia/Sydney'
    >>> aus_user.timezone.now()
    datetime.datetime(2016, 6, 21, 9, 47, 4, 29965, tzinfo=<DstTzInfo 'Australia/Sydney' AEST+10:00:00 STD>)
    >>> aus_user.timezone.today()
    datetime.date(2016, 6, 21)
    
    >>> us_user = User.objects.get(timezone='US/Eastern')
    >>> us_user.timezone.name
    'US/Eastern'
    >>> us_user.timezone.now()
    datetime.datetime(2016, 6, 20, 19, 47, 4, 32814, tzinfo=<DstTzInfo 'US/Eastern' EDT-1 day, 20:00:00 DST>)
    >>> us_user.timezone.today()
    datetime.date(2016, 6, 20)

.. warning::
    
    Be careful when dealing with local times. Django recommends you "use UTC in the code and use local time only when interacting with end users", with the conversion from UTC to local time usually only being performed in templates. And the pytz documentation notes "The preferred way of dealing with times is to always work in UTC, converting to localtime only when generating output to be read by humans". See the `Django timezone documentation <https://docs.djangoproject.com/en/1.9/topics/i18n/timezones/>`_ and the `pytz documentation <http://pytz.sourceforge.net/>`_.