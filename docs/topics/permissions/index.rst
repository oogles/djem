========================
Object-Level Permissions
========================

Django's permissions framework has the foundation for, but no implementation of, object-level permissions (OLP). The permissions it supports apply to *all* records of a particular model - hence they are "model-level" permissions (MLP). For example, using the standard Django "polls" application to illustrate, you can use the Django permissions framework to determine if any given user can change ``Question``\ s, but not to determine if they can change a given ``Question`` in particular.

Djem provides a very simple implementation of an OLP system, described in the following sections:

.. toctree::
    :maxdepth: 2

    intro
    checking
    advanced
