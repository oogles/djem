=======================
Form Classes and Mixins
=======================

.. module:: djem.forms.bases

.. currentmodule:: djem.forms

``UserSavable``
===============

.. versionadded:: 0.7

.. autoclass:: UserSavable


``AuditableForm``
=================

.. versionchanged:: 0.7

    Renamed from ``CommonInfoForm``. The old name is still available for backwards compatibility, but is considered deprecated.

.. autoclass:: AuditableForm

    .. attribute:: user

        The user model instance provided to the constructor on instantiation. May be ``None`` on unbound forms.
