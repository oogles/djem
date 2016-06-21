========
Settings
========

The following settings can be added to your project's ``settings.py`` file to customise the behaviour of Django Goodies.

.. _setting-GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE:

``GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE``
============================================

.. versionadded:: 0.4

Default: ``True``

By default, the :meth:`~django_goodies.models.CommonInfoMixin.save` method of :class:`~django_goodies.models.CommonInfoMixin` and the :meth:`~django_goodies.models.managers.CommonInfoQuerySet.update` method of :class:`~django_goodies.models.managers.CommonInfoQuerySet` require their first positional argument to be a ``User`` instance, so they can automatically set the ``user_created`` and/or ``user_modified`` fields that ``CommonInfoMixin`` provides. This behaviour can cause issues if you are using third party code that calls the ``save`` method of a model instance or the ``update`` method of a queryset, as it will not pass this required argument.

Django Goodies provides :class:`~django_goodies.forms.CommonInfoForm` to enable Django ``ModelForms`` to work with models making use of ``CommonInfoMixin``. But if you can't use similar wrappers around other third party code invoking these methods, this setting can help.

Setting ``GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE`` to ``False`` removes the "required" nature of the ``user`` argument to :meth:`~django_goodies.models.CommonInfoMixin.save`/:meth:`~django_goodies.models.managers.CommonInfoQuerySet.update`. It will still be accepted, and will still be used as per usual if it is provided. But if it is not provided, no exception will be raised, and the fields that would ordinarily be populated by it will simply be left alone.

.. warning::
    
    The ``user_created`` and ``user_modified`` fields will still be required. When creating instances of models using ``CommonInfoMixin``, and a ``User`` is not passed to the :meth:`~django_goodies.models.CommonInfoMixin.save` method, these fields will need to be populated manually, or an ``IntegrityError`` will be raised.

.. warning::
    
    Using this setting can reduce the accuracy of ``user_modified``, as it is no longer guaranteed to be updated by any save/update to the model instance. It will be up to you to ensure that this field is updated when necessary.
