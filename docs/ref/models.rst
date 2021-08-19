==========================
Model Mixins and QuerySets
==========================

.. module:: djem.models.models

.. py:currentmodule:: djem.models

Mixins
======

``Loggable``
------------

.. versionadded:: 0.7

.. autoclass:: Loggable

    Adds :doc:`instance-based logging <../topics/logging>` support to any model.

    .. automethod:: start_log
    .. automethod:: end_log
    .. automethod:: discard_log
    .. automethod:: log
    .. automethod:: get_log
    .. automethod:: get_last_log

``OLPMixin``
------------

.. versionadded:: 0.7

.. autoclass:: OLPMixin

    Inherits instance-based logging functionality from :class:`Loggable`. For more information on the available features, see :doc:`../topics/permissions/advanced`.

    .. method:: has_perm(perm, obj=None)

        A replacement for the default ``has_perm()`` method defined by Django's ``PermissionsMixin``.

        In conjunction with the :setting:`DJEM_UNIVERSAL_OLP` setting, this version can force superusers to be subject to the same object-level permissions checks as regular users.

        In conjunction with the :setting:`DJEM_PERM_LOG_VERBOSITY`, an automatic log of all permission checks can be kept, using :doc:`instance-based logging <../topics/logging>`.

    .. automethod:: clear_perm_cache

``Auditable``
-------------

.. versionchanged:: 0.7

    Renamed from ``CommonInfoMixin``. The old name is still available for backwards compatibility, but is considered deprecated.

.. class:: Auditable()

    ``Auditable`` is a model mixin class that provides:

    * Standard user and datetime fields: ``user_created``, ``user_modified``, ``date_created``, ``date_modified``.
    * An overridden ``objects`` Manager that provides access to the custom :class:`AuditableQuerySet`.
    * Support for :ref:`auditable-ownership-checking` on an instance and via :class:`AuditableQuerySet`.

    .. automethod:: save
    .. automethod:: owned_by

.. seealso::

    :class:`AuditableQuerySet`
        The custom QuerySet used by ``Auditable``.

    :class:`~djem.forms.AuditableForm`
        A ``ModelForm`` subclass that supports ``Auditable`` models.

    :class:`~djem.forms.UserSavable`
        A ``ModelForm`` mixin to add support for ``Auditable`` models, for forms that already have a known user.

``Archivable``
--------------

.. versionchanged:: 0.7

    Renamed from ``ArchivableMixin``. The old name is still available for backwards compatibility, but is considered deprecated.

.. class:: Archivable()

    ``Archivable`` is a model mixin class that provides:

    * An ``is_archived`` Boolean field, defaulting to ``False``.
    * An overridden ``objects`` Manager that provides access to the custom :class:`ArchivableQuerySet`.
    * Methods for :ref:`archiving and unarchiving <archivable-archiving-unarchiving>`

    .. automethod:: archive
    .. automethod:: unarchive

.. seealso::

    :class:`ArchivableQuerySet`
        The custom QuerySet used by ``Archivable``.

``Versionable``
---------------

.. versionchanged:: 0.7

    Renamed from ``VersioningMixin``. The old name is still available for backwards compatibility, but is considered deprecated.

.. class:: Versionable()

    ``Versionable`` is a model mixin class that provides:

    * A ``version`` field that is automatically incremented on every save.
    * An overridden ``objects`` Manager that provides access to the custom :class:`VersionableQuerySet`.

    .. automethod:: save

    .. exception:: Versionable.AmbiguousVersionError

        A subclass of :exc:`~djem.exceptions.ModelAmbiguousVersionError` specific to the :class:`Versionable` class. Raised when attempting to access the ``version`` field after it has been atomically incremented.

.. seealso::

    :class:`VersionableQuerySet`
        The custom QuerySet used by ``Versionable``.


QuerySets
=========

``MixableQuerySet``
-------------------

.. versionadded:: 0.7

.. autoclass:: MixableQuerySet

    .. automethod:: as_manager


``AuditableQuerySet``
---------------------

.. versionchanged:: 0.7

    Renamed from ``CommonInfoQuerySet``. The old name is still available for backwards compatibility, but is considered deprecated.

.. autoclass:: AuditableQuerySet

    .. method:: as_manager

        See :meth:`MixableQuerySet.as_manager`.

    .. automethod:: create

        .. versionadded:: 0.7

    .. automethod:: get_or_create

        .. versionadded:: 0.7

    .. automethod:: update
    .. automethod:: update_or_create

        .. versionadded:: 0.7

    .. automethod:: owned_by


``ArchivableQuerySet``
----------------------

.. autoclass:: ArchivableQuerySet

    .. method:: as_manager

        See :meth:`MixableQuerySet.as_manager`.

    .. automethod:: archived

        .. versionadded:: 0.7

    .. automethod:: unarchived

        .. versionadded:: 0.7


``VersionableQuerySet``
-----------------------

.. versionchanged:: 0.7

    Renamed from ``VersioningQuerySet``. The old name is still available for backwards compatibility, but is considered deprecated.

.. autoclass:: VersionableQuerySet

    .. method:: as_manager

        See :meth:`MixableQuerySet.as_manager`.

    .. automethod:: update


``StaticAbstract``
==================

.. class:: StaticAbstract()

    ``StaticAbstract`` is a combination of :class:`Auditable`, :class:`Archivable` and :class:`Versionable`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields and functionality offered by each of the mixins.
