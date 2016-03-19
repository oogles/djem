============================
Model Managers and QuerySets
============================

.. module:: django_goodies.models.managers

The following Managers and QuerySets support the :doc:`various mixins and base classes<models>` provided by Django Goodies.

``CommonInfoManager``
=====================

.. class:: CommonInfoManager()

    ``CommonInfoManager`` is a custom manager for :class:`~django_goodies.models.CommonInfoMixin` that simply provides access to :class:`CommonInfoQuerySet`.

``CommonInfoQuerySet``
======================

.. class:: CommonInfoQuerySet(\*args, \*\*kwargs)
    
    ``CommonInfoQuerySet`` provides custom functionality pertaining to the fields provided by :class:`~django_goodies.models.CommonInfoMixin`.
    
    .. automethod:: update
    .. automethod:: owned_by

``ArchivableManager``
=====================

.. class:: ArchivableManager(archived=None)

    ``ArchivableManager`` is a custom manager for :class:`~django_goodies.models.ArchivableMixin`. ``archive`` is a flag used to dictate the default filter applied on the ``is_archived`` field provided by ``ArchivableMixin``. When given as ``None``, no filter will be applied (the manager behaviour will not be altered). When given as ``True`` or ``False``, the default queryset provided by the manager will be filtered to archived or unarchived records, respectively.
    
    ``ArchivableManager`` provides access to :class:`ArchivableQuerySet`.

``ArchivableQuerySet``
======================

.. class:: ArchivableQuerySet(\*args, \*\*kwargs)
    
    ``ArchivableQuerySet`` provides custom functionality pertaining to the ``is_archived`` field provided by :class:`~django_goodies.models.ArchivableMixin`.
    
    .. automethod:: archive
    .. automethod:: unarchive

``VersioningManager``
=====================

.. class:: VersioningManager()

    ``VersioningManager`` is a custom manager for :class:`~django_goodies.models.VersioningMixin` that simply provides access to :class:`VersioningQuerySet`.

``VersioningQuerySet``
======================

.. class:: VersioningQuerySet(\*args, \*\*kwargs)
    
    ``VersioningQuerySet`` provides custom functionality pertaining to the ``version`` field provided by :class:`~django_goodies.models.VersioningMixin`.
    
    .. automethod:: update
