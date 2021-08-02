=================
Form Base Classes
=================

.. module:: djem.forms.bases

.. currentmodule:: djem.forms

``CommonInfoForm``
==================

.. class:: CommonInfoForm(\*args, user=None, \*\*kwargs)

    ``CommonInfoForm`` is a Django ``ModelForm`` that is customised to allow it to work with :class:`~djem.models.Auditable`. ``Auditable`` overrides the model instance's ``save`` method and adds a required ``user`` argument, so it can keep its ``user_modified`` field up to date as changes are made to the instance. This prevents it being used with a standard ``ModelForm``, as the form's ``save`` method will attempt to call the model instance's ``save`` method without the ``user`` argument.

    ``CommonInfoForm`` overrides the form's ``save`` method so that it *does* call the instance's ``save`` method with a ``user`` argument. It also overrides the form's constructor to accept a ``user`` keyword argument on instantiation, so it has a known ``user`` to use in the ``save`` method. The ``user`` argument of the constructor is only *required* when the form is bound - as this is the only time ``save`` would be called - but it is always accepted. And subclasses of ``CommonInfoForm`` may well choose to make use of the ``user`` argument in other ways, when the form is bound or not. Best practice would be to always instantiate a ``CommonInfoForm`` with a ``user`` keyword argument.
