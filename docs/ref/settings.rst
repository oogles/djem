========
Settings
========

The following settings can be added to your project's ``settings.py`` file to customise the behaviour of Djem features.


.. setting:: DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE

``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE``
=========================================

.. versionadded:: 0.4

Default: ``True``

By default, the :meth:`~djem.models.CommonInfoMixin.save` method of :class:`~djem.models.CommonInfoMixin` and the :meth:`~djem.models.managers.CommonInfoQuerySet.update` method of :class:`~djem.models.managers.CommonInfoQuerySet` require their first positional argument to be a ``User`` instance, so they can automatically set the ``user_created`` and/or ``user_modified`` fields that ``CommonInfoMixin`` provides. This behaviour can cause issues if you are using third party code that calls the ``save`` method of a model instance or the ``update`` method of a queryset, as it will not pass this required argument.

Djem provides :class:`~djem.forms.CommonInfoForm` to enable Django ``ModelForms`` to work with models making use of ``CommonInfoMixin``. But if you can't use similar wrappers around other third party code invoking these methods, this setting can help.

Setting ``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE`` to ``False`` removes the "required" nature of the ``user`` argument to :meth:`~djem.models.CommonInfoMixin.save`/:meth:`~djem.models.managers.CommonInfoQuerySet.update`. It will still be accepted, and will still be used as per usual if it is provided. But if it is not provided, no exception will be raised, and the fields that would ordinarily be populated by it will simply be left alone.

.. warning::

    The ``user_created`` and ``user_modified`` fields will still be required. When creating instances of models using ``CommonInfoMixin``, and a ``User`` is not passed to the :meth:`~djem.models.CommonInfoMixin.save` method, these fields will need to be populated manually, or an ``IntegrityError`` will be raised.

.. warning::

    Using this setting can reduce the accuracy of ``user_modified``, as it is no longer guaranteed to be updated by any save/update to the model instance. It will be up to you to ensure that this field is updated when necessary.


.. setting:: DJEM_DEFAULT_403

``DJEM_DEFAULT_403``
====================

.. versionadded:: 0.5

Default: False

Specifies the default behaviour of the :func:`~djem.auth.permission_required` decorator and :class:`djem.auth.PermissionRequired` class-based view mixin when a user does not have the specified permission/s. If ``True``, the ``PermissionDenied`` exception will be raised, invoking the 403 handler. If ``False``, the user will be redirected to the appropriate login url.

This affects default behaviour only - individual uses of :func:`~djem.auth.permission_required` and :class:`djem.auth.PermissionRequired` can customise it.


.. setting:: DJEM_DEFAULT_PAGE_LENGTH

``DJEM_DEFAULT_PAGE_LENGTH``
============================

.. versionadded:: 0.5

Default: None

The default page length to use for the :func:`djem.pagination.get_page` helper function. Adding this setting removes the need to provide a page length argument to every :func:`djem.pagination.get_page` call. See :ref:`pagination-page-length` for more details.


.. setting:: DJEM_FORM_FIELD_TAG

``DJEM_FORM_FIELD_TAG``
=======================

.. versionadded:: 0.6

.. currentmodule:: djem.templatetags.djem

Default: 'div'

The HTML tag to use for the wrapping element rendered around form fields when using the :ttag:`form_field` or :ttag:`checkbox` template tags.
