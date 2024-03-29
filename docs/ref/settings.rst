========
Settings
========

The following settings can be added to your project's ``settings.py`` file to customise the behaviour of Djem features.


.. setting:: DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE

``DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE``
=======================================

.. versionchanged:: 0.7

    Renamed from ``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE``. The old setting is still available for backwards compatibility, but is considered deprecated.

Default: ``True``

By default, the :meth:`~djem.models.Auditable.save` method of :class:`~djem.models.Auditable` and various methods of :class:`~djem.models.AuditableQuerySet` (e.g. :meth:`~djem.models.AuditableQuerySet.create`, :meth:`~djem.models.AuditableQuerySet.update`, etc) require being passed a user model instance, so they can automatically set the ``user_created`` and/or ``user_modified`` fields that ``Auditable`` provides. This behaviour can cause issues if you are using third party code that calls any of these methods, as it will not pass this required argument.

Djem provides :class:`~djem.forms.AuditableForm` and :class:`~djem.forms.UserSavable` to enable Django ``ModelForms`` to work with models making use of ``Auditable``. But if you can't use similar wrappers around other third party code invoking these methods, this setting can help.

Setting ``DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE`` to ``False`` removes the "required" nature of this additional user argument. It will still be accepted, and will still be used as per usual if it is provided. But if it is not provided, no exception will be raised, and the fields that would ordinarily be populated by it will simply be left alone.

.. warning::

    The ``user_created`` and ``user_modified`` fields will still be required. When creating instances of models using ``Auditable``, and a user instance is not passed to the :meth:`~djem.models.Auditable.save` method, these fields will need to be populated manually, or an ``IntegrityError`` will be raised.

.. warning::

    Using this setting can reduce the accuracy of ``user_modified``, as it is no longer guaranteed to be updated by any save/update to the model instance. It will be up to you to ensure that this field is updated when necessary.


.. setting:: DJEM_DEFAULT_403

``DJEM_DEFAULT_403``
====================

.. versionadded:: 0.5

Default: ``False``

Specifies the default behaviour of the :func:`~djem.auth.permission_required` decorator and :class:`djem.auth.PermissionRequired` class-based view mixin when a user does not have the specified permission/s. If ``True``, the ``PermissionDenied`` exception will be raised, invoking the 403 handler. If ``False``, the user will be redirected to the appropriate login url.

This affects default behaviour only - individual uses of :func:`~djem.auth.permission_required` and :class:`djem.auth.PermissionRequired` can customise it.


.. setting:: DJEM_DEFAULT_PAGE_LENGTH

``DJEM_DEFAULT_PAGE_LENGTH``
============================

.. versionadded:: 0.5

Default: ``None``

The default page length to use for the :func:`djem.pagination.get_page` helper function. Adding this setting removes the need to provide a page length argument to every :func:`djem.pagination.get_page` call. See :ref:`pagination-page-length` for more details.


.. setting:: DJEM_FORM_FIELD_TAG

``DJEM_FORM_FIELD_TAG``
=======================

.. versionadded:: 0.6

.. currentmodule:: djem.templatetags.djem

Default: ``'div'``

The HTML tag to use for the wrapping element rendered around form fields when using the :ttag:`form_field` or :ttag:`checkbox` template tags.


.. setting:: DJEM_UNIVERSAL_OLP

``DJEM_UNIVERSAL_OLP``
======================

.. versionadded:: 0.7

.. currentmodule:: djem.models

Default: ``False``

In conjunction with a custom user model including :class:`OLPMixin`, setting this to ``True`` enables support for forcing superusers to undergo the same object-level permissions checking that regular users do, allowing OLP logic to actually *deny* permissions to superusers where relevant.


.. setting:: DJEM_PERM_LOG_VERBOSITY

``DJEM_PERM_LOG_VERBOSITY``
===========================

.. versionadded:: 0.7

.. currentmodule:: djem.models

Default: ``0``

In conjunction with a custom user model including :class:`OLPMixin`, this setting controls the level of :ref:`automatic permission logging <permissions-advanced-logging>` performed by :meth:`OLPMixin.has_perm`:

* ``0``: No automatic logging
* ``1``: Logs are automatically created for each permission check, with minimal automatic entries
* ``2``: Logs are automatically created for each permission check, with more informative automatic entries

In addition to the automatic entries, a value of ``1`` or ``2`` allow manual log entries to be added from within object-level access methods with no need to manually start/finish any logs.
