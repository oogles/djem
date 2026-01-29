======
Models
======

.. currentmodule:: djem.models

Djem provides a series of custom classes to support common model-related functionality, including models, model managers and model fields.


.. _auditable:

Auditable
=========

The :class:`Auditable` class is designed as a mixin for Django models, providing:

* Standard user and datetime fields: ``user_created``, ``user_modified``, ``date_created``, ``date_modified``.
* Support for :ref:`ensuring these fields remain accurate <auditable-maintaining-accuracy>` as records are updated over time.
* Support for :ref:`ownership checking <auditable-ownership-checking>`.
* A custom manager/queryset to assist with maintaining accuracy and checking ownership.

.. versionchanged:: 0.7

    The :class:`Auditable` mixin was previously called ``CommonInfoMixin``. The old name is still available for backwards compatibility, but is considered deprecated.

.. warning::

    Using :class:`Auditable` can break code that automatically calls methods such as the model's :meth:`~Auditable.save` method, or the queryset's :meth:`~AuditableQuerySet.update` method. See :ref:`Auditable-maintaining-accuracy` for a description of the caveats of ``Auditable``, and workarounds.

Usage
-----

To make use of :class:`Auditable`, simply include it among your model's parent classes. It should be listed ahead of ``models.Model``:

.. code-block:: python

    from django.db import models
    from djem.models import Auditable

    class ExampleModel(Auditable, models.Model):

        name = models.CharField(max_length=64)

Default values
--------------

The ``date_created`` and ``date_modified`` fields will default to ``django.utils.timezone.now()`` at the moment the instance is initially saved.

The ``user_created`` and ``user_modified`` fields will require a ``User`` instance in order to populate their values. However, they do not need to be populated manually. Djem provides various mechanisms to both make it easy to populate these fields automatically, and to ensure they are populated any time a record is updated. See :ref:`auditable-maintaining-accuracy`.

If any of the fields *are* populated manually, those values will take precedence.

.. _auditable-maintaining-accuracy:

Maintaining accuracy
--------------------

The fields provided by :class:`Auditable` are designed to be automatically populated whenever necessary. And in the case of ``date_modified`` and ``user_modified``, it is necessary to update them whenever a record is updated.

For the date fields, this is easy to accomplish. For the user fields, it requires something extra - knowledge of the user doing the creating/updating.

Various means exist to provide this:

Calling ``save()`` on the instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`Auditable.save` method is overridden to require a ``User`` instance as the first argument. This allows the method to populate ``user_created`` when a new instance is being created, and keep ``user_modified`` up to date as changes are made.

.. code-block:: python

    >>> alice = User.objects.get(username='alice')
    >>> bob = User.objects.get(username='bob')
    >>> obj = ExampleModel(name='Awesome Example')
    >>> obj.user_created
    None
    >>> obj.save(alice)
    >>> obj.user_created.username
    "alice"
    >>> obj.user_modified.username
    "alice"
    >>> obj.save(bob)
    >>> obj.user_created.username
    "alice"
    >>> obj.user_modified.username
    "bob"

.. note::

    These fields will be updated even if the :meth:`~Auditable.save` method is passed a sequence of ``update_fields`` that does not include it (see `Django documentation for update_fields <https://docs.djangoproject.com/en/stable/ref/models/instances/#specifying-which-fields-to-save>`_). They will simply be appended to the list.

Using the queryset
~~~~~~~~~~~~~~~~~~

Like :meth:`Auditable.save`, various methods on :class:`AuditableQuerySet` are also overridden to require an additional argument providing a user model instance. Again, this allows the methods to set or update the user-based fields as necessary. These methods include :meth:`~AuditableQuerySet.create`, :meth:`~AuditableQuerySet.get_or_create`, :meth:`~AuditableQuerySet.update`, and :meth:`~AuditableQuerySet.update_or_create`.

The following demonstrates the use of the :meth:`~AuditableQuerySet.create` and :meth:`~AuditableQuerySet.update` methods:

.. code-block:: python

    >>> alice = User.objects.get(username='alice')
    >>> bob = User.objects.get(username='bob')
    >>> obj = ExampleModel.objects.create(alice, name='Good Example')
    >>> obj.user_created.username
    'alice'
    >>> obj.user_modified.username
    'alice'
    >>> ExampleModel.objects.filter(name='Good Example').update(bob, name='Great Example')
    >>> obj.refresh_from_db()
    >>> obj.user_created.username
    'alice'
    >>> obj.user_modified.username
    'bob'

.. versionadded:: 0.7

    The :meth:`~AuditableQuerySet.create`, :meth:`~AuditableQuerySet.get_or_create`, and :meth:`~AuditableQuerySet.update_or_create` queryset methods.

Using forms
~~~~~~~~~~~

The ``ModelForm`` is core to any Django web application. For compatibility with :class:`Auditable` (i.e. ensuring a ``user`` argument is passed to the :meth:`Auditable.save` method), Djem provides :class:`~djem.forms.AuditableForm` and :class:`~djem.forms.UserSavable`.

:class:`~djem.forms.AuditableForm` is a simple wrapper around ``ModelForm``, and is designed to be used as a replacement to it for forms based on ``Auditable`` models. It takes a ``User`` instance as a constructor argument, giving it a known user to pass to the model's ``save()`` method when the form is saved.

.. code-block:: python

    # forms.py
    from djem.forms import AuditableForm

    class ExampleForm(AuditableForm):

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

Alternatively, :class:`~djem.forms.UserSavable` is a mixin for ``ModelForm``, and is designed to be used for forms that already accept and store a known user. Unlike :class:`~djem.forms.AuditableForm`, it does not modify the constructor, but does assume a ``self.user`` attribute is available to pass to the model's ``save()`` method when the form is saved.

.. code-block:: python

    # forms.py
    from django import forms
    from djem.forms import UserSavable

    class ExampleForm(UserSavable, forms.ModelForm):

        def __init__(self, *args, user=None, **kwargs):

            self.user = user

            super().__init__(*args, **kwargs)

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

.. versionchanged:: 0.7

    :class:`~djem.forms.AuditableForm` was previously called ``CommonInfoForm``. The old name is still available for backwards compatibility, but is considered deprecated.

.. versionadded:: 0.7

    :class:`~djem.forms.UserSavable`

Caveats and workarounds
~~~~~~~~~~~~~~~~~~~~~~~

Obviously any code that calls a model's ``save()`` method or various queryset methods (such as ``create()`` or ``update()``) will need to be altered to pass a user argument for models that incorporate :class:`Auditable`. This may not always be possible for third party code. :class:`~djem.forms.AuditableForm`/:class:`~djem.forms.UserSavable` solve this problem for one common occurrence, by providing wrappers around Django's ``ModelForm.save()`` method, but there are plenty of others.

If it is not feasible to customise code that calls these methods, it *is* possible to disable the requirement of the ``user`` argument. This can be done by setting :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` to ``False`` in ``settings.py``:

.. code-block:: python

    DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE = False

This allows the use of ``Auditable`` and all related functionality without the strict requirement of passing the ``user`` argument to methods that save/update the record. If passed, it will still be used as described above, but not providing it will not raise an exception. Of course, the methods won't automatically populate the appropriate fields, either. This means that ``user_created`` and ``user_modified`` will need to be manually populated when creating, and ``user_modified`` will need to be manually populated when updating.

.. versionchanged:: 0.7

    :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` was previously called ``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE``. The old setting is still available for backwards compatibility, but is considered deprecated.

.. warning::

    Setting :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` to ``False`` reduces the accuracy of the ``user_modified`` field, as it cannot be guaranteed that the user that made a change was recorded.

.. note::

    If using tools to automate the creation of records in tests - such as `Django Dynamic Fixture <https://django-dynamic-fixture.readthedocs.io/en/latest/>`_, `Model Bakery <https://model-bakery.readthedocs.io/en/latest/>`_, etc - the :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` setting can be overridden to allow these tools to dynamically generate records without needing to provide a ``user`` argument. However, be careful to selectively override the setting only during creation of these records, not for entire tests, as this may mask bugs in the code being tested. If the ``user`` argument is typically required outside a test environment, but has been missed, tests may pass incorrectly.
    
    Prefer using `SimpleTestCase.settings() <https://docs.djangoproject.com/en/stable/topics/testing/tools/#django.test.SimpleTestCase.settings>`_ rather than `override_settings() <https://docs.djangoproject.com/en/stable/topics/testing/tools/#django.test.override_settings>`_ to disable the ``user`` argument requirement:
    
    .. code-block:: python
        
        from django.test import TestCase
        
        class ExampleTestCase(TestCase):
            
            def test_something(self):
                
                # Create test records without requiring `user` argument
                with self.settings(DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE=False):
                    obj = ... # dynamic record creation
                
                # Test code without masking missing `user` arguments
                do_something(obj)

An additional caveat is that there may not always be a known user when a change is being made to a ``Auditable`` record, e.g. during a system-triggered background process. Situations such as these may be solved by setting :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` as described above, and taking responsibility for keeping ``user_modified`` up to date when necessary, or by creating a "system" user that can be passed in during these operations.


.. _auditable-ownership-checking:

Ownership checking
------------------

:class:`Auditable` also adds support for *ownership checking*. The :meth:`~Auditable.owned_by` method can be called on an model instance to check if the instance is owned by the given user. The user can be provided either as a ``User`` instance or as the primary key of a ``User`` record.

.. code-block:: python

    >>> alice = User.objects.get(username='alice')
    >>> bob = User.objects.get(username='bob')
    >>> obj = ExampleModel(name='Awesome Example')
    >>> obj.save(alice)
    >>> obj.owned_by(alice)
    True
    >>> obj.owned_by(bob)
    False

Ownership checking is also available via a ``Auditable`` model's manager and queryset. The queryset's :meth:`~AuditableQuerySet.owned_by` method also accepts a user as a ``User`` instance or as the primary key of a ``User`` record. It returns a queryset filtered to records where the ``user_created`` field matches the given user.

.. code-block:: python

    >>> ExampleModel.objects.owned_by(alice)
    [<ExampleModel: Awesome Example>]
    >>> ExampleModel.objects.owned_by(bob)
    []
    >>> ExampleModel.objects.filter(name__contains='Great').owned_by(alice)
    []


.. _archivable:

Archivable
==========

The :class:`Archivable` class is designed as a mixin for Django models, providing:

* An ``is_archived`` Boolean field, defaulting to ``False``.
* A custom manager/queryset with shortcuts for filtering on the ``is_archived`` field.
* Support for easily :ref:`archiving and unarchiving <archivable-archiving-unarchiving>` an instance.

.. versionchanged:: 0.7

    The :class:`Archivable` mixin was previously called ``ArchivableMixin``. The old name is still available for backwards compatibility, but is considered deprecated.

Usage
-----

To make use of :class:`Archivable`, simply include it among your model's parent classes. It should be listed ahead of ``models.Model``:

.. code-block:: python

    from django.db import models
    from djem.models import Archivable

    class ExampleModel(Archivable, models.Model):

        name = models.CharField(max_length=64)

.. _archivable-archiving-unarchiving:

Archiving and unarchiving
-------------------------

Instances of :class:`Archivable` have the :meth:`~Archivable.archive` and :meth:`~Archivable.unarchive` methods. These set the ``is_archived`` flag of the instance to ``True`` or ``False``, respectively, and save the instance. Any arguments provided to them are passed through to their internal calls to ``save()``.

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

.. versionchanged:: 0.7
    Previous versions of Djem also provided ``archive()`` and ``unarchive()`` methods on :class:`ArchivableQuerySet`. These were removed due to the overhead they added to combining the functionality of :class:`ArchivableQuerySet` and :class:`AuditableQuerySet`, and because the naming was too similar after the introduction of the :meth:`~ArchivableQuerySet.archived` and :meth:`~ArchivableQuerySet.unarchived` methods. Using the ``update()`` method and passing ``is_archived`` is more explicit and safer.

Filtering shortcuts
-------------------

:class:`Archivable` uses the custom :class:`ArchivableQuerySet`, which provides the :meth:`~ArchivableQuerySet.archived` and :meth:`~ArchivableQuerySet.unarchived` methods. These methods filter the queryset to records with ``is_archived=True`` or ``is_archived=False``, respectively. They are accessible both at the manager and queryset level.

.. code-block:: python

    >>> ExampleModel(name='Example1', is_archived=True).save()
    >>> ExampleModel(name='Example2', is_archived=False).save()
    >>> ExampleModel.objects.count()
    2
    >>> ExampleModel.objects.unarchived().count()
    1
    >>> ExampleModel.objects.filter(name='Example1').unarchived().count()
    0
    >>> ExampleModel.objects.archived().count()
    1
    >>> ExampleModel.objects.filter(name='Example2').archived().count()
    0

.. versionchanged:: 0.7
    Previous versions of Djem used three different managers - ``objects``, ``live`` and ``archived`` - to provide access to querysets with various preset filters on the ``is_archived`` field. This didn't allow for applying the filters if a queryset was obtained by other means (e.g. via a ``ManyToManyField`` related manager) and made it more difficult to extend the manager (if the model inheriting from ``Archivable`` needed its own custom manager/queryset).


.. _versionable:

Versionable
===========

The :class:`Versionable` class is designed as a mixin for Django models, providing a ``version`` field that is automatically incremented on every save.

.. versionchanged:: 0.7

    The :class:`Versionable` mixin was previously called ``VersioningMixin``. The old name is still available for backwards compatibility, but is considered deprecated.

Usage
-----

To make use of :class:`Versionable`, simply include it among your model's parent classes. It should be listed ahead of ``models.Model``:

.. code-block:: python

    from django.db import models
    from djem.models import Versionable

    class ExampleModel(Versionable, models.Model):

        name = models.CharField(max_length=64)

.. _versionable-incrementing-version:

Incrementing ``version``
------------------------

Incrementation of the ``version`` field is done atomically, through the use of a Django ``F()`` expression, to avoid possible race conditions. See `Django documentation for F() expressions <https://docs.djangoproject.com/en/stable/ref/models/expressions/#django.db.models.F>`_.

To ensure the ``version`` field is always kept current, :class:`Versionable` overrides the :meth:`~Versionable.save` method and the :meth:`~VersionableQuerySet.update` method of its custom queryset. The ``update_or_create()`` method, while not overridden, will also increment the version appropriately.

.. note::

    The ``version`` field will be updated even if the ``save()`` method is passed a sequence of ``update_fields`` that does not include it (see `Django documentation for update_fields <https://docs.djangoproject.com/en/stable/ref/models/instances/#specifying-which-fields-to-save>`_). It will simply be appended to the list.

.. warning::

    Once an instance is saved and the ``F()`` expression is used to increment the version, the ``version`` field will become a Django ``Expression`` instance. At this point, it is no longer accessible as an integer. For the same reason an ``F()`` expression is used to perform the incrementation (race conditions), the new version cannot be retrieved from the database after the save and used to replace the ``Expression`` value. There is the possibility the version retrieved will not be the one that matches the rest of the values on the model. The only way to regain a usable ``version`` field after saving a model instance is requerying for the whole instance.
    Attempting to access the ``version`` field after it has been incremented will raise a :exc:`Versionable.AmbiguousVersionError` exception.

.. note::

    Even though directly accessing the ``version`` field is not possible after it has been atomically incremented, subsequent saves of the same instance will continue to correctly increment it.


Mixing Mixins
=============

A model can include any combination of the above mixins. However, since they all use custom managers/querysets to provide additional functionality unique to them, a model using multiple mixins will also need to specify its own manager/queryset that incorporates the functionality of each. The custom querysets have been designed to make this as simple as possible, without any additional customisation necessary. Each mixin supports a custom :meth:`~MixableQuerySet.as_manager` method that makes it even easier, as demonstrated below. This functionality is provided by the :class:`MixableQuerySet` mixin, which is also available for use in your own custom queryset classes.

For a ready-made combination of all three mixins (:ref:`auditable`, :ref:`archivable` and :ref:`versionable`), see :ref:`staticabstract`.

The following is an example of a model using both the :ref:`auditable` and :ref:`archivable` mixins:

.. code-block:: python

    from django.db import models
    from djem.models import Archivable, Auditable
    from djem.managers import ArchivableQuerySet, AuditableQuerySet

    class ExampleModel(Auditable, Archivable, models.Model):

        name = models.CharField(max_length=64)

        objects = AuditableQuerySet.as_manager(ArchivableQuerySet)

.. versionadded:: 0.7

    :class:`MixableQuerySet` and its custom :meth:`~MixableQuerySet.as_manager` method. Previously, mixin querysets had to be combined manually.


.. _staticabstract:

StaticAbstract
==============

:class:`StaticAbstract` is a combination of :ref:`auditable`, :ref:`archivable` and :ref:`versionable`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields and functionality offered by each of the mixins, including:

* :ref:`Maintaining the accuracy <auditable-maintaining-accuracy>` of ``date_modified`` and ``user_modified`` as changes are made.
* Automatically and :ref:`atomically incrementing <versionable-incrementing-version>` ``version`` as changes are made.
* Allowing :ref:`archiving and unarchiving <archivable-archiving-unarchiving>`.
* Providing :ref:`ownership checking <auditable-ownership-checking>`.

Usage
-----

To make use of :class:`StaticAbstract`, simply inherit from it:

.. code-block:: python

    from django.db import models
    from djem.models import StaticAbstract

    class ExampleModel(StaticAbstract):

        name = models.CharField(max_length=64)


TimeZoneField
=============

:class:`TimeZoneField` is a model field that stores timezone name strings ('Australia/Sydney', 'US/Eastern', etc) in the database and provides access to :class:`~djem.utils.dt.TimeZoneHelper` instances for the stored timezones, as :ref:`explained below <timezonefield-timezonehelper>`.

In forms, a :class:`TimeZoneField` is represented by a ``TypedChoiceField``, and rendered using a ``Select`` widget by default.

.. versionchanged:: 0.9

    The :class:`TimeZoneField` now uses the standard library's `zoneinfo <https://docs.python.org/3/library/zoneinfo.html#module-zoneinfo>`_ package. It previously required the third party `pytz <http://pytz.sourceforge.net/>`_ library to be installed.

.. note::

    Use of :class:`TimeZoneField` only makes sense if `USE_TZ <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-USE_TZ>`_ is True.

Usage
-----

:class:`TimeZoneField` is used just like any model field. The following demonstrates adding a ``time_zone`` field to a custom ``User`` model.

.. code-block:: python

    from django.contrib.auth.models import AbstractBaseUser
    from djem.models import TimeZoneField

    class User(AbstractBaseUser):
        ...
        time_zone = TimeZoneField()

Accessing the ``time_zone`` field on a ``User`` instance yields a :class:`~djem.utils.dt.TimeZoneHelper` instance, which provides some helpers for dealing with times in local timezones, as :ref:`explained below <timezonefield-timezonehelper>`.

.. code-block:: python

    >>> user = User.objects.get(timezone='Australia/Sydney')
    >>> user.timezone
    <TimeZoneHelper: Australia/Sydney>

Available Timezones
-------------------

:class:`TimeZoneField` is a reasonably light wrapper around a ``CharField``, providing a default value for the ``choices`` argument. The default choices are taken from `pytz.common_timezones <http://pytz.sourceforge.net/#helpers>`_.

These choices can be modified in the same way as any other ``CharField``. However, they need to be valid timezone name strings as recognised by ``zoneinfo``, which references either system timezone data or, on systems that have no available timezone data, the separate `tzdata <https://pypi.org/project/tzdata/>`_ package.

For example, using a very limited set of timezones:

.. code-block:: python

    from django.contrib.auth.models import AbstractBaseUser
    from djem.models import TimeZoneField

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

:class:`~djem.utils.dt.TimeZoneHelper` is a simple helper class that provides shortcuts for getting the current date and the current datetime for a known local timezone.

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

    Be careful when dealing with local times. Django recommends you "use UTC in the code and use local time only when interacting with end users", with the conversion from UTC to local time usually only being performed in templates. And the pytz documentation notes "The preferred way of dealing with times is to always work in UTC, converting to localtime only when generating output to be read by humans". See the `Django timezone documentation <https://docs.djangoproject.com/en/stable/topics/i18n/timezones/>`_ and the `pytz documentation <http://pytz.sourceforge.net/>`_.
