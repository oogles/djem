=============================
Model Mixins and Base Classes
=============================

.. module:: djem.models

``CommonInfoMixin``
===================

.. class:: CommonInfoMixin()

    ``CommonInfoMixin`` is a model mixin class that provides:

    * Standard user and datetime fields: ``user_created``, ``user_modified``, ``date_created``, ``date_modified``.
    * An overridden ``objects`` Manager, an instance of the custom :class:`~djem.models.managers.CommonInfoManager` that provides access to the custom :class:`~djem.models.managers.CommonInfoQuerySet`.
    * Support for :ref:`commoninfomixin-ownership-checking` on an instance and via ``CommonInfoQuerySet``.
    * A simple :ref:`default implementation <commoninfomixin-object-permissions>` of :doc:`/topics/permissions` via ownership checking.

    .. automethod:: save
    .. automethod:: owned_by

.. seealso::

    :class:`~djem.models.managers.CommonInfoManager`
        The custom Manager exposed by the ``objects`` attribute.

    :class:`~djem.models.managers.CommonInfoQuerySet`
        The custom QuerySet exposed by ``CommonInfoManager``.

    :class:`~djem.forms.CommonInfoForm`
        A ``ModelForm`` subclass to act as a base for ``CommonInfoMixin`` model forms.


``ArchivableMixin``
===================

.. class:: ArchivableMixin()

    ``ArchivableMixin`` is a model mixin class that provides:

    * An ``is_archived`` Boolean field, defaulting to ``False``.
    * An overridden ``objects`` Manager, an instance of the custom :class:`~djem.models.managers.ArchivableManager` that provides access to the custom :class:`~djem.models.managers.ArchivableQuerySet`.
    * Two additional managers, ``live`` and ``archived``, with default querysets filtered to unarchived (``is_archived == False``) and archived (``is_archived == True``) records by default. Both are also instances of :class:`~djem.models.managers.ArchivableManager`.
    * Support for :ref:`archiving and unarchiving <archivablemixin-archiving-unarchiving>`, both at the instance level and in bulk via :class:`~djem.models.managers.ArchivableQuerySet`.

    .. automethod:: archive
    .. automethod:: unarchive

.. seealso::

    :class:`~djem.models.managers.ArchivableManager`
        The custom Manager exposed by the ``objects``, ``live`` and ``archived`` attributes.

    :class:`~djem.models.managers.ArchivableQuerySet`
        The custom QuerySet exposed by ``ArchivableManager``.


``VersioningMixin``
===================

.. class:: VersioningMixin()

    ``VersioningMixin`` is a model mixin class that provides:

    * A ``version`` field that is automatically incremented on every save.
    * An overridden ``objects`` Manager, an instance of the custom :class:`~djem.models.managers.VersioningManager` that provides access to the custom :class:`~djem.models.managers.VersioningQuerySet`.

    .. automethod:: save

    .. exception:: VersioningMixin.AmbiguousVersionError

        A subclass of :exc:`~djem.exceptions.ModelAmbiguousVersionError` specific to the :class:`VersioningMixin` class. Raised when attempting to access the ``version`` field after it has been atomically incremented.

.. seealso::

    :class:`~djem.models.managers.VersioningManager`
        The custom Manager exposed by the ``objects`` attribute.

    :class:`~djem.models.managers.VersioningQuerySet`
        The custom QuerySet exposed by ``VersioningManager``.


``StaticAbstract``
==================

.. class:: StaticAbstract()

    ``StaticAbstract`` is a combination of :class:`CommonInfoMixin`, :class:`ArchivableMixin` and :class:`VersioningMixin`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields, as well as custom ``objects``, ``live`` and ``archived`` managers, and provides access to all the functionality offered by each of the mixins.
