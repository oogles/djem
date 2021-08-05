=======================
Form Classes and Mixins
=======================

.. module:: djem.forms.bases

.. currentmodule:: djem.forms

``UserSavable``
===============

.. autoclass:: UserSavable


``AuditableForm``
=================

.. autoclass:: AuditableForm

    .. attribute:: user

        The user model instance provided to the constructor on instantiation. May be ``None`` on unbound forms.
