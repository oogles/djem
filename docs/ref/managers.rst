============================
Model Managers and QuerySets
============================

.. module:: djem.models.managers

The following Managers and QuerySets support the :doc:`various mixins and base classes<models>` provided by Djem.

``CommonInfoManager``
=====================

.. class:: CommonInfoManager()

    ``CommonInfoManager`` is a custom manager for :class:`~djem.models.CommonInfoMixin` that simply provides access to :class:`CommonInfoQuerySet`.

``CommonInfoQuerySet``
======================

.. class:: CommonInfoQuerySet(\*args, \*\*kwargs)

    ``CommonInfoQuerySet`` provides custom functionality pertaining to the fields provided by :class:`~djem.models.CommonInfoMixin`.

    .. automethod:: update
    .. automethod:: owned_by

``ArchivableManager``
=====================

.. class:: ArchivableManager(archived=None)

    ``ArchivableManager`` is a custom manager for :class:`~djem.models.ArchivableMixin`. The constructor argument ``archived`` is a flag used to dictate the default filter applied on the ``is_archived`` field provided by :class:`~djem.models.ArchivableMixin`. When given as ``None``, no filter will be applied (the manager behaviour will not be altered). When given as ``True`` or ``False``, the default queryset provided by the manager will be filtered to archived or unarchived records, respectively.

    ``ArchivableManager`` provides access to :class:`ArchivableQuerySet`.

``ArchivableQuerySet``
======================

.. class:: ArchivableQuerySet(\*args, \*\*kwargs)

    ``ArchivableQuerySet`` provides custom functionality pertaining to the ``is_archived`` field provided by :class:`~djem.models.ArchivableMixin`.

    .. automethod:: archive
    .. automethod:: unarchive

``VersioningManager``
=====================

.. class:: VersioningManager()

    ``VersioningManager`` is a custom manager for :class:`~djem.models.VersioningMixin` that simply provides access to :class:`VersioningQuerySet`.

``VersioningQuerySet``
======================

.. class:: VersioningQuerySet(\*args, \*\*kwargs)

    ``VersioningQuerySet`` provides custom functionality pertaining to the ``version`` field provided by :class:`~djem.models.VersioningMixin`.

    .. automethod:: update
