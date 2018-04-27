==========================
Model Mixins and QuerySets
==========================

.. module:: djem.models

Mixins
======

``CommonInfoMixin``
-------------------

.. class:: CommonInfoMixin()

    ``CommonInfoMixin`` is a model mixin class that provides:

    * Standard user and datetime fields: ``user_created``, ``user_modified``, ``date_created``, ``date_modified``.
    * An overridden ``objects`` Manager that provides access to the custom :class:`CommonInfoQuerySet`.
    * Support for :ref:`commoninfomixin-ownership-checking` on an instance and via :class:`CommonInfoQuerySet`.

    .. automethod:: save
    .. automethod:: owned_by

.. seealso::

    :class:`CommonInfoQuerySet`
        The custom QuerySet used by ``CommonInfoMixin``.

    :class:`~djem.forms.CommonInfoForm`
        A ``ModelForm`` subclass to act as a base for ``CommonInfoMixin`` model forms.

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

``CommonInfoQuerySet``
----------------------

.. class:: CommonInfoQuerySet(\*args, \*\*kwargs)

    ``CommonInfoQuerySet`` provides custom functionality pertaining to the fields provided by :class:`~djem.models.CommonInfoMixin`.

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

    ``StaticAbstract`` is a combination of :class:`CommonInfoMixin`, :class:`ArchivableMixin` and :class:`VersioningMixin`. It is designed as an abstract base class for models, rather than a mixin itself. It includes all the fields and functionality offered by each of the mixins.
