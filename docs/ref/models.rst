=============================
Model Mixins and Base Classes
=============================

.. module:: django_goodies.models

Django Goodies provides a series of model mixin classes that provide default fields, methods and/or managers for common model functionality.

``CommonInfoMixin``
===================

.. class:: CommonInfoMixin()

``CommonInfoMixin`` is a model mixin class that provides:

* Standard user and datetime fields: ``user_created``, ``user_modified``, ``date_created``, ``date_modified``.
* An overridden ``objects`` Manager, an instance of the custom :class:`~django_goodies.managers.CommonInfoManager` that provides access to the custom :class:`~django_goodies.managers.CommonInfoQuerySet`.
* Support for :ref:`ownership-checking` on an instance and via ``CommonInfoQuerySet``.

To make use of ``CommonInfoMixin``, simply include it among your model's parent classes:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import CommonInfoMixin
    
    class ExampleModel(CommonInfoMixin, models.Model):
        
        name = models.CharField(max_length=64)

Default values
--------------

The ``date_created`` and ``date_modified`` fields will default to the datetime at the moment the instance is initially saved.

The ``user_created`` and ``user_modified`` fields will require a ``User`` instance in order to populate their values. However, they do not need to be provided manually. The :meth:`~CommonInfoMixin.save` method of ``CommonInfoMixin`` is overridden to require a ``User`` argument. See :ref:`saving-commoninfomixin`.

.. _saving-commoninfomixin:

Saving
------

To ensure the ``user_modified`` and ``date_modified`` fields are always kept current, ``CommonInfoMixin`` overrides the :meth:`~CommonInfoMixin.save` method and the :meth:`~django_goodies.managers.CommonInfoQuerySet.update` method of the custom manager/queryset.
Both methods are modified to take a ``User`` instance as a required argument.

.. note::
    
    These fields will be updated even if the ``save`` method is passed a sequence of ``update_fields`` that does not include it (see `Django documentation for update_fields <https://docs.djangoproject.com/en/stable/ref/models/instances/#specifying-which-fields-to-save>`_). They will simply be appended to the list.

.. warning::
    
    Models incorporating this mixin are prevented from being involved in any process that automatically calls :meth:`~CommonInfoMixin.save` on the instance, or :meth:`~django_goodies.managers.CommonInfoQuerySet.update` on the manager/queryset, as it won't pass the required ``user`` argument. For example, the queryset methods ``create`` and ``get_or_create`` will fail, as will saves performed by ModelForms that aren't overridden to support the special syntax.

.. _ownership-checking:

Ownership checking
------------------

The mixin also adds support for *ownership checking*. The :meth:`~CommonInfoMixin.owned_by` method can be called on an model instance to check if the instance is owned by the given user. The user can be provided either as a ``User`` instance or as the primary key of a ``User`` record.

For example, using ownership checking in a view:

.. code-block:: python
    
    def my_view(request, some_id):
        
        some_instance = ExampleModel.objects.get(pk=some_id)
        
        if not some_instance.owned_by(request.user):
            messages.error(request, 'You are not the owner')

The :class:`~django_goodies.managers.CommonInfoQuerySet` also adds an :meth:`~django_goodies.managers.CommonInfoQuerySet.owned_by` method. It also accepts a user as a ``User`` instance or as the primary key of a ``User`` record. It returns a queryset filtered to records where the ``user_created`` field matches the given user.

Methods
-------

.. automethod:: CommonInfoMixin.save
.. automethod:: CommonInfoMixin.owned_by

.. seealso::
    
    :class:`~django_goodies.managers.CommonInfoManager`
        The custom Manager exposed by the ``objects`` attribute.
    
    :class:`~django_goodies.managers.CommonInfoQuerySet`
        The custom QuerySet exposed by ``CommonInfoManager``.


``ArchivableMixin``
===================

.. class:: ArchivableMixin()

``ArchivableMixin`` is a model mixin class that provides:

* An ``is_archived`` Boolean field, defaulting to ``False``.
* An overridden ``objects`` Manager, an instance of the custom :class:`~django_goodies.managers.ArchivableManager` that provides access to the custom :class:`~django_goodies.managers.ArchivableQuerySet`.
* Two additional managers, ``live`` and ``archived``, with default querysets filtered to unarchived (``is_archived == False``) and archived (``is_archived == True``) records by default. Both are also instances of ``ArchivableManager``.
* Support for :ref:`archiving-unarchiving`, both at the instance level and in bulk via ``ArchivableQuerySet``.

To make use of ``ArchivableMixin``, simply include it among your model's parent classes:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import ArchivableMixin
    
    class ExampleModel(ArchivableMixin, models.Model):
        
        name = models.CharField(max_length=64)

The managers
------------

``ArchivableMixin`` provides three managers: ``objects``, ``live`` and ``archived``.

All three are instances of :class:`~django_goodies.managers.ArchivableManager`, and so provide access to the custom :class:`~django_goodies.managers.ArchivableQuerySet`. ``ArchivableQuerySet`` provides methods for custom bulk operations. See :ref:`archiving-unarchiving`.

The three differ in the default querysets they provide:

- ``objects`` provides access to all records, as per usual
- ``live`` filters to records with the ``is_archived`` flag set to ``False``
- ``archived`` filters to records with the ``is_archived`` flag set to ``True``

.. code-block:: python
    
    >>> ExampleModel(name='test1', is_archived=True).save()
    >>> ExampleModel(name='test2', is_archived=False).save()
    >>> ExampleModel.objects.count()
    2
    >>> ExampleModel.live.count()
    1
    >>> ExampleModel.archived.count()
    1

.. _archiving-unarchiving:

Archiving and unarchiving
-------------------------

Instances of ``ArchivableMixin`` have the :meth:`~ArchivableMixin.archive` and :meth:`~ArchivableMixin.unarchive` methods. These set the ``is_archived`` flag of the instance to ``True`` or ``False``, respectively, and save the instance. Any arguments are passed through to the call to ``save``.

.. code-block:: python
    
    >>> instance = ExampleModel(name='test')
    >>> instance.save()
    >>> ExampleModel.objects.get(name='test').is_archived
    False
    >>> instance.archive()
    >>> ExampleModel.objects.get(name='test').is_archived
    True
    >>> instance.unarchive()
    >>> ExampleModel.objects.get(name='test').is_archived
    False

All three managers (``objects``, ``live`` and ``archived``) also provide access to the bulk :meth:`~django_goodies.managers.ArchivableQuerySet.archive` and :meth:`~django_goodies.managers.ArchivableQuerySet.unarchive` methods of ``ArchivableQuerySet``.

.. code-block:: python
    
    >>> ExampleModel(name='test1', is_archived=True).save()
    >>> ExampleModel(name='test2', is_archived=False).save()
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
    
    ``ArchivableManager`` does not provide access to these methods directly. Like ``delete``, ``archive`` and ``unarchive`` are only accessible via a QuerySet.
    
    .. code-block:: python
        
        # incorrect - won't work
        >>> ExampleModel.objects.archive()
        
        # correct
        >>> ExampleModel.objects.all().archive()


Methods
-------

.. automethod:: ArchivableMixin.archive
.. automethod:: ArchivableMixin.unarchive

.. seealso::
    
    :class:`~django_goodies.managers.ArchivableManager`
        The custom Manager exposed by the ``objects``, ``live`` and ``archived`` attributes.
    
    :class:`~django_goodies.managers.ArchivableQuerySet`
        The custom QuerySet exposed by ``ArchivableManager``.



``VersioningMixin``
===================

.. class:: VersioningMixin()

``VersioningMixin`` is a model mixin class that provides:

* A ``version`` field that is automatically incremented on every save.
* An overridden ``objects`` Manager, an instance of the custom :class:`~django_goodies.managers.VersioningManager` that provides access to the custom :class:`~django_goodies.managers.VersioningQuerySet`.

To make use of ``VersioningMixin``, simply include it among your model's parent classes:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import VersioningMixin
    
    class ExampleModel(VersioningMixin, models.Model):
        
        name = models.CharField(max_length=64)

Incrementing ``version``
------------------------

Incrementation of the ``version`` field is done atomically, through the use of a Django ``F()`` expression, to avoid possible race conditions. See `Django documentation for F() expressions <https://docs.djangoproject.com/en/stable/ref/models/expressions/#django.db.models.F>`_.

To ensure the ``version`` field is always kept current, ``VersioningMixin`` overrides the :meth:`~VersioningMixin.save` method and the :meth:`~django_goodies.managers.VersioningQuerySet.update` method of the custom manager/queryset.

.. note::
    
    The ``version`` field will be updated even if the ``save`` method is passed a sequence of ``update_fields`` that does not include it (see `Django documentation for update_fields <https://docs.djangoproject.com/en/stable/ref/models/instances/#specifying-which-fields-to-save>`_). They will simply be appended to the list.

.. warning::
    
    Once an instance is saved and the ``F()`` expression is used to increment the version, the ``version`` field will become a Django ``Expression`` instance. At this point, it is no longer accessible as an integer. For the same reason an ``F()`` expression is used to perform the incrementation (race conditions), the new version cannot be retrieved from the database after the save and used to replace the ``Expression`` value. There is the possibility the version retrieved will not be the one that matches the rest of the values on the model. The only way to regain a usable ``version`` field after saving a model instance is requerying for the whole instance.
    Attempting to access the ``version`` field after it has been incremented will raise a :exc:`VersioningMixin.AmbiguousVersionError` exception.

.. note::
    
    Even though directly accessing the ``version`` field is not possible after it has been atomically incremented, subsequent saves of the same instance will continue to correctly increment it.

``AmbiguousVersionError``
-------------------------

.. exception:: VersioningMixin.AmbiguousVersionError
    
    A subclass of :exc:`~django_goodies.exceptions.ModelAmbiguousVersionError` specific to the ``VersioningMixin`` class. Raised when attempting to access the ``version`` field after it has been atomically incremented.

Methods
-------

.. automethod:: VersioningMixin.save

.. seealso::
    
    :class:`~django_goodies.managers.VersioningManager`
        The custom Manager exposed by the ``objects`` attribute.
    
    :class:`~django_goodies.managers.VersioningQuerySet`
        The custom QuerySet exposed by ``VersioningManager``.


Mixing Mixins
=============

A model can include any combination of the above mixins. However, since they all use custom managers to provide additional functionality unique to them, a model using multiple mixins will need to provide its own manager that incorporates the functionality of each. For most mixins, this is only necessary for ``objects``, but for :class:`ArchivableMixin`, the ``live`` and ``archived`` managers will also need to be customised.

The following is an example of a model using the :class:`CommonInfoMixin` and :class:`ArchivableMixin`.

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import CommonInfoMixin, ArchivableMixin
    from django_goodies.managers import (
        CommonInfoManager, CommonInfoQuerySet, ArchivableManager, ArchivableQuerySet
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

For a ready-made combination of all three mixins (:class:`CommonInfoMixin`, :class:`ArchivableMixin` and :class:`VersioningMixin`), see :class:`StaticAbstract`.

``StaticAbstract``
==================

.. class:: StaticAbstract()

``StaticAbstract`` is a combination of :class:`CommonInfoMixin`, :class:`ArchivableMixin` and :class:`VersioningMixin`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields, as well as custom ``objects``, ``live`` and ``archived`` managers, and provides access to all the functionality offered by each of the mixins.

To make use of ``StaticAbstract``, simply inherit from it:

.. code-block:: python
    
    from django.db import models
    from django_goodies.models import StaticAbstract
    
    class ExampleModel(StaticAbstract):
        
        name = models.CharField(max_length=64)
