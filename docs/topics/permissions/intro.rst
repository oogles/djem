============
Introduction
============

.. currentmodule:: djem.auth

Djem's object-level permission (OLP) system provides following features:

* As with model-level permissions, an object-level permission may be granted to a user based on the ``User`` object itself, or based on a ``Group`` to which the user belongs.
* Permissions are only checked at the object level if the user has the model-level permission. That is, a user must be able to change ``Question``\ s in general if they are to be granted permission to change a particular ``Question``.
* Methods on the object itself grant or deny the permission, based on self-contained logic. The database is not required to store links between users/groups and individual model objects.

.. note::

    Djem's OLP system is simply an extension of the default Django permissions system. As such, it expects the ``User`` model to have the same attributes and methods that power that system. If you are using a custom user model (as is recommended), it should either inherit from ``AbstractUser`` or include the ``PermissionsMixin`` to be compatible. See the Django documentation for `custom user models and permissions <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#custom-users-and-permissions>`_.


Enabling
========

Basic usage of object-level permissions is enabled simply by including the custom :class:`djem.auth.ObjectPermissionsBackend` authentication backend in the ``AUTHENTICATION_BACKENDS`` setting:

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'djem.auth.ObjectPermissionsBackend'
    ]

See the Django  `documentation on authentication backends <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#specifying-authentication-backends>`__ for more information.

More advanced features require additional steps. These are outlined in :doc:`advanced`.


Supported permissions
=====================

Any existing permission can be used with the OLP system, though it may not make sense for all of them. For example, Django provides default "add" permissions for all models. It doesn't make sense for adding to involve object-level permissions, as no object would yet exist on which to *check* for an "add" permission. That being said, the OLP system contains no logic preventing you from using *any* permission at the object level.

If the default Django-provided permissions ("add", "change" and "delete") aren't enough, you can add custom permissions via the ``permissions`` attribute of a model's inner ``Meta`` class, as per the `Django documentation <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#custom-permissions>`_.

Any permissions added this way are automatically supported by the OLP system. You just need to define the necessary methods on the model class, :ref:`as described below <permissions-defining>`. And remember: a user must have the standard, model-level permission before object-level permissions will even be checked.


.. _permissions-defining:

Defining permissions
====================

Object-level permissions are ultimately determined by specially-named methods on the object in question. These are the object-level *access methods*. The two types of access methods are:

* ``_user_can_<permission_name>(self, user)``: Grant/deny permission based on the given ``User`` instance by returning ``True`` or ``False``, respectively.
* ``_group_can_<permission_name>(self, groups)``: Grant/deny permission based on the given ``Group`` queryset by returning ``True`` or ``False``, respectively.

For the Django default "change" permission on the ``polls.Question`` model, the method names would be: ``_user_can_change_question()`` and ``_group_can_change_question()``.

When defining custom permissions, the permission name used in the method names must be the same as that provided in the ``permissions`` attribute of the model's ``Meta`` class. If *either* of the methods returns ``True``, the user is granted the permission.

The following example demonstrates how to define a model that uses object-level permissions for a custom permission. It uses a modified version of the ``Question`` model `created in the Django tutorial <https://docs.djangoproject.com/en/stable/intro/tutorial02/#creating-models>`_ that only allows voting by explicitly defined users.

.. code-block:: python

    from django.conf import settings
    from django.db import models

    class Question(models.Model):

        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')
        allowed_voters = models.ManyToManyField(settings.AUTH_USER_MODEL)

        def _user_can_vote_on_question(self, user):

            return self.allowed_voters.filter(pk=user.pk).exists()

        class Meta:
            permissions = (('vote_on_question', 'Can vote on question'),)

.. note::

    The :class:`ObjectPermissionsBackend` handles calling these methods when necessary - they should never need to be called manually. See :doc:`checking`.

.. note::

    These object-level access methods can raise ``PermissionDenied`` and it will be treated as if they returned ``False``. Regardless of whether the user-based or group-based check raises the exception, the other could still grant the permission.

.. _permissions-default:

Permissions default open
========================

An important concept in Djem's OLP system is that permissions default *open* at the object level. That is to say, unless explicit logic is given to dictate how an object-level permission should be granted/denied, it is assumed to be granted. As such, an OLP check on an object with no defined object-level access methods is equivalent to a model-level check for the same permission.

This makes the system interchangeable with the default Django permissions system. Common code can check permissions at the object level and will be unaffected if no object-level access control exists for a given model - it doesn't need to pick and choose whether to use object-level or model-level permission checking.
