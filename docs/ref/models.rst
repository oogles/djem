==========================
Model Mixins and QuerySets
==========================

.. module:: djem.models.models

.. py:currentmodule:: djem.models

Mixins
======

``LogMixin``
------------

.. autoclass:: LogMixin

    Adds :doc:`instance-based logging <../topics/logging>` support to any model.

    .. versionadded:: 0.7

    .. automethod:: start_log
    .. automethod:: end_log
    .. automethod:: discard_log
    .. automethod:: log
    .. automethod:: get_log
    .. automethod:: get_last_log

``OLPMixin``
------------

.. class:: OLPMixin

    .. versionadded:: 0.7

    A mixin for a custom user model that enables additional :doc:`advanced features <../topics/permissions/advanced>` of the object-level permission system.

    Inherits instance-based logging functionality from :class:`LogMixin`.

    .. method:: has_perm(perm, obj=None)

        A replacement for the default ``has_perm()`` method defined by Django's ``PermissionsMixin``.

        In conjunction with the :setting:`DJEM_UNIVERSAL_OLP` setting, this version can force superusers to be subject to the same object-level permissions checks as regular users.

        In conjunction with the :setting:`DJEM_PERM_LOG_VERBOSITY`, an automatic log of all permission checks can be kept, using :doc:`instance-based logging <../topics/logging>`.

    .. automethod:: clear_perm_cache

``Auditable``
-------------

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

    :class:`~djem.forms.UserSaveMixin`
        A ``ModelForm`` mixin to add support for ``Auditable`` models, for forms that already have a known user.

``ArchivableMixin``
-------------------

.. class:: ArchivableMixin()

    ``ArchivableMixin`` is a model mixin class that provides:

    * An ``is_archived`` Boolean field, defaulting to ``False``.
    * An overridden ``objects`` Manager that provides access to the custom :class:`ArchivableQuerySet`.
    * Support for :ref:`archiving and unarchiving <archivablemixin-archiving-unarchiving>`, both at the instance level and in bulk via :class:`ArchivableQuerySet`.

    .. automethod:: archive
    .. automethod:: unarchive

.. seealso::

    :class:`ArchivableQuerySet`
        The custom QuerySet used by ``ArchivableMixin``.

``VersioningMixin``
-------------------

.. class:: VersioningMixin()

    ``VersioningMixin`` is a model mixin class that provides:

    * A ``version`` field that is automatically incremented on every save.
    * An overridden ``objects`` Manager that provides access to the custom :class:`VersioningQuerySet`.

    .. automethod:: save

    .. exception:: VersioningMixin.AmbiguousVersionError

        A subclass of :exc:`~djem.exceptions.ModelAmbiguousVersionError` specific to the :class:`VersioningMixin` class. Raised when attempting to access the ``version`` field after it has been atomically incremented.

.. seealso::

    :class:`VersioningQuerySet`
        The custom QuerySet used by ``VersioningMixin``.


QuerySets
=========

``AuditableQuerySet``
---------------------

.. class:: AuditableQuerySet(\*args, \*\*kwargs)

    ``AuditableQuerySet`` provides custom functionality pertaining to the fields provided by :class:`~djem.models.Auditable`.

    .. automethod:: update
    .. automethod:: owned_by


``ArchivableQuerySet``
----------------------

.. class:: ArchivableQuerySet(\*args, \*\*kwargs)

    ``ArchivableQuerySet`` provides custom functionality pertaining to the ``is_archived`` field provided by :class:`~djem.models.ArchivableMixin`.

    .. automethod:: archived

        .. versionadded:: 0.7

    .. automethod:: unarchived

        .. versionadded:: 0.7


``VersioningQuerySet``
----------------------

.. class:: VersioningQuerySet(\*args, \*\*kwargs)

    ``VersioningQuerySet`` provides custom functionality pertaining to the ``version`` field provided by :class:`~djem.models.VersioningMixin`.

    .. automethod:: update


``StaticAbstract``
==================

.. class:: StaticAbstract()

    ``StaticAbstract`` is a combination of :class:`Auditable`, :class:`ArchivableMixin` and :class:`VersioningMixin`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields and functionality offered by each of the mixins.
