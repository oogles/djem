========================
Object-Level Permissions
========================

Django's permissions framework has the foundation, but no implementation, for object-level permissions. For example, using the standard Django "polls" application to illustrate, you can use the Django permissions framework to determine if any given user can change ``Questions``, but not to determine if they can change a given ``Question`` in particular.

Django Goodies provides a very simple implementation of an object-level permissions system with the following features:

* As with model-level permissions, an object-level permission may be granted to a user based on the ``User`` object itself, or based on a ``Group`` to which the user belongs.
* Permissions are only checked at the object level if the user has the model-level permission. That is, a user must be able to change ``Questions`` in general if they are to be granted permission to change a particular ``Question``.
* Methods on the object itself grant or deny the permission, based on self-contained logic. The database is not required to store links between users/groups and individual model objects.

.. note::
    
    Just as with the Django permissions framework, the object-level permissions systems expects the ``User`` model to have certain attributes and methods. If you are using a custom user model, it will need to include the ``PermissionsMixin`` to be compatible. See the Django documentation for `custom user models and permissions <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#custom-users-and-permissions>`_.


Supported permissions
=====================

Any existing permission can be used with the object-level permissions system, though it may not make sense for all of them. For example, Django provides default "add" permissions for all models. It doesn't make sense for adding to involve object-level permissions, as no object yet exists on which to *check* permissions. That being said, the object-level permissions system contains no logic preventing you from using the "add" permission, or any other permission, at the object level.

If the default Django-provided permissions ("add", "change" and "delete") aren't enough, you can add custom permissions via the ``permissions`` attribute of a model's inner ``Meta`` class - see the `Django documentation <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#custom-permissions>`__.

Any permissions added this way are automatically supported by the object-level permissions system. You just need to define the necessary methods on the ``Model`` class, :ref:`as described below <permissions-defining>`. And remember: a user must have the standard, model-level permission before object-level permissions will even be checked. It does not matter *how* the user is granted the model-level permission, as long as they have it. That is, it may be granted to the user specifically, or to any one of the groups they belong to. 


Usage
=====

Enabling
--------

Use of object-level permissions is enabled simply by including the custom ``django_goodies.auth.ObjectPermissionsBackend`` authentication backend in the ``AUTHENTICATION_BACKENDS`` setting:

.. code-block:: python
    
    AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'django_goodies.auth.ObjectPermissionsBackend']

See the `Django documentation <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#specifying-authentication-backends>`__ for more information.

.. _permissions-defining:

Defining
--------

Object-level permissions are ultimately determined by specially-named methods on the object in question. The two types of methods are:

* ``_user_can_<permission_name>(self, user)``: Grant/deny permission based on the given ``User`` instance by returning ``True`` or ``False``, respectively.
* ``_group_can_<permission_name>(self, groups)``: Grant/deny permission based on the given ``Group`` queryset by returning ``True`` or ``False``, respectively.

For the Django default "change" permission on the ``polls.Question`` model, the method names would be: ``_user_can_change_question`` and ``_group_can_change_question``.

When defining custom permissions, the permission name used in the method names must be the same as that provided in the ``permissions`` attribute of the model's ``Meta`` class.

The ``django_goodies.auth.ObjectPermissionsBackend`` handles calling these methods - they should never need to be called manually.

The following example demonstrates how to define a model that uses object-level permissions for a custom permission. It uses an updated version of the ``Question`` model `created in the Django tutorial <https://docs.djangoproject.com/en/stable/intro/tutorial02/#creating-models>`_ that only allows voting by explicitly defined users.

.. code-block:: python
    
    from django.conf import settings
    from django.db import models
    
    class Question(models.Model):
        
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')
        voters = models.ManyToManyField(settings.AUTH_USER_MODEL)
        
        def _user_can_vote_on_question(self, user):
            
            return self.voters.filter(pk=user.pk).exists()
        
        class Meta:
            permissions = (('vote_on_question', 'Can vote on question'),)

Checking permissions
--------------------

The two main ways of using the object-level permissions system to check a user's permissions on a specific object are via a ``User`` instance and via the ``ifperm`` and ``ifnotperm`` template tags.

Both of these approaches use the standard Django permissions framework and rely on the custom ``django_goodies.auth.ObjectPermissionsBackend`` to call the appropriate ``_user_can_<permission_name>``/``_group_can_<permission_name>`` methods. In the examples below, each permission check will result in ``_user_can_<permission_name>`` being called and provided the ``User`` instance involved in the check, and ``_group_can_<permission_name>`` being called and provided with a queryset of all ``Groups`` to which that user belongs. Either method can return ``True`` to grant the user permission.

Checking via ``User`` instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``has_perm`` method provided by Django's ``User`` model (or by ``PermissionsMixin`` if using a custom user model) accepts an optional ``obj`` argument. Django does nothing with it by default, but passing it will invoke Django Goodies' object-level permissions system. Thus it can be used to check a user's object-level permissions on a given object.

Continuing with the modified ``Question`` model defined above:

.. code-block:: python
    
    >>> user = User.objects.get(username='bill')
    >>> question = Question.objects.filter(voters=bill).first()
    >>> user.has_perm('vote_on_question', question)
    True
    
    >>> question = Question.objects.exclude(voters=bill).first()
    >>> user.has_perm('vote_on_question', question)
    False

See Django documentation for `User <https://docs.djangoproject.com/en/stable/ref/contrib/auth/#methods>`_ and `PermissionsMixin <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#django.contrib.auth.models.PermissionsMixin>`_.

.. note::
    
    Object-level permissions will only be checked if the user also has the appropriate model-level permissions. In the example above, it is assumed the user has ``vote_on_question`` permission at the model level.

.. note::
    
    In addition to ``has_perm``, the ``has_perms``, ``get_group_permissions`` and ``get_all_permissions`` methods on ``User``/``PermissionMixin`` also accept the optional ``obj`` argument and work with the object-level permissions system.

Checking in templates
~~~~~~~~~~~~~~~~~~~~~

Checking object-level permissions in a Django template can be done using the :ref:`tags-ifperm` and :ref:`tags-ifnotperm` template tags. These are block tags whose content is displayed if the permissions check passes. For :ref:`tags-ifperm`, it passes if the user *has* the permission. For :ref:`tags-ifnotperm`, it passes if the user *does not* have the permission. Each tag supports an ``else`` block, whose content is displayed if the permissions check fails.

Each tag must be passed a user instance, the name of the permission to check and the object to check it on.

.. code-block:: html+django
    
    {% load goodies %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% else %}
        You do not have permission to vote on this question.
    {% endifperm %}
    ...

.. code-block:: html+django
    
    {% load goodies %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% else %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifnotperm %}
    ...


Caching
=======

Like ``ModelBackend`` `does for model-level permissions <https://docs.djangoproject.com/en/stable/topics/auth/default/#permission-caching>`_, the ``django_goodies.auth.ObjectPermissionsBackend`` caches object-level permissions on the ``User`` object after the first time they are checked. Unlike ``ModelBackend``, the user's entire set of object-level permissions are not determined and cached on this first access, only the specific permission being tested, for the specific object given.

This caching system has the same advantages and disadvantages as that used for model-level permissions. Multiple checks of the same permission (on the same object) in the same request will only need to execute the (possibly expensive) logic in your ``_user_can_<permission_name>``/``_group_can_<permission_name>`` methods once. However, that means that if something changes within the request that would alter the state of a permission, and that permission has already been checked, the ``User`` object will not immediately reflect the new state of the permission - a new instance of the ``User`` would need to be queried from the database. Exactly what *might* affect the state of a permission depends entirely upon the logic implemented in the ``_user_can_<permission_name>``/``_group_can_<permission_name>`` methods, so this is something to be aware of both while writing these methods and while using them.
