========================
Object-Level Permissions
========================

.. currentmodule:: djem.auth

Django's permissions framework has the foundation for, but no implementation of, object-level permissions. For example, using the standard Django "polls" application to illustrate, you can use the Django permissions framework to determine if any given user can change ``Questions``, but not to determine if they can change a given ``Question`` in particular.

Djem provides a very simple implementation of an object-level permissions system with the following features:

* As with model-level permissions, an object-level permission may be granted to a user based on the ``User`` object itself, or based on a ``Group`` to which the user belongs.
* Permissions are only checked at the object level if the user has the model-level permission. That is, a user must be able to change ``Questions`` in general if they are to be granted permission to change a particular ``Question``.
* Methods on the object itself grant or deny the permission, based on self-contained logic. The database is not required to store links between users/groups and individual model objects.

.. note::

    Just as with the Django permissions framework, the object-level permissions systems expects the ``User`` model to have certain attributes and methods. If you are using a custom user model, it will need to include the ``PermissionsMixin`` to be compatible. See the Django documentation for `custom user models and permissions <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#custom-users-and-permissions>`_.


Enabling
========

Use of object-level permissions is enabled simply by including the custom :class:`djem.auth.ObjectPermissionsBackend` authentication backend in the ``AUTHENTICATION_BACKENDS`` setting:

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'djem.auth.ObjectPermissionsBackend'
    ]

See the Django  `documentation on authentication backends <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#specifying-authentication-backends>`__ for more information.

.. versionadded:: 0.4
    :class:`ObjectPermissionsBackend`


Supported permissions
=====================

Any existing permission can be used with the object-level permissions system, though it may not make sense for all of them. For example, Django provides default "add" permissions for all models. It doesn't make sense for adding to involve object-level permissions, as no object would yet exist on which to *check* for an "add" permission. That being said, the object-level permissions system contains no logic preventing you from using *any* permission at the object level.

If the default Django-provided permissions ("add", "change" and "delete") aren't enough, you can add custom permissions via the ``permissions`` attribute of a model's inner ``Meta`` class, as per the `Django documentation <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#custom-permissions>`_.

Any permissions added this way are automatically supported by the object-level permissions system. You just need to define the necessary methods on the model class, :ref:`as described below <permissions-defining>`. And remember: a user must have the standard, model-level permission before object-level permissions will even be checked. It does not matter *how* the user is granted the model-level permission, as long as they have it. That is, it may be granted to the user specifically, or to any one of the groups they belong to.


.. _permissions-defining:

Defining permissions
====================

Object-level permissions are ultimately determined by specially-named methods on the object in question. The two types of methods are:

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

    The :class:`ObjectPermissionsBackend` handles calling these methods when necessary - they should never need to be called manually.

.. note::

    These object-level access methods can raise ``PermissionDenied`` and it will be treated as if they returned ``False``. Regardless of whether the user-based or group-based check raises the exception, the other could still grant the permission.

.. _permissions-default:

Permissions default open
------------------------

An important concept in Djem's object-level permissions system is that permissions default *open* at the object level. That is to say, unless explicit logic is given to dictate how an object-level permission should be granted/denied, it is assumed to be granted. As such, an object-level permission check on an object with no defined object-level access methods is equivalent to a model-level permission check for the same permission.

This makes the system interchangeable with the existing Django permissions system. Common code can check permissions at the object level and will be unaffected if no object-level access control exists for a given model - it doesn't need to pick and choose whether to use object-level or model-level permission checking.


Checking permissions
====================

The main ways of using the object-level permissions system to check a user's permissions on a specific object are:

* the ``permission_required`` decorator for function-based views or ``PermissionRequiredMixin`` mixin for class-based views
* the ``ifperm`` and ``ifnotperm`` template tags
* the ``has_perm()`` method on a ``User`` instance

All of these approaches use the standard Django permissions framework and rely on the custom :class:`ObjectPermissionsBackend` to call the appropriate ``_user_can_<permission_name>``/``_group_can_<permission_name>`` methods. In the examples below, each permission check will result in ``_user_can_<permission_name>`` being called and provided the ``User`` instance involved in the check, and ``_group_can_<permission_name>`` being called and provided with a queryset of all ``Groups`` to which that user belongs. Either method can return ``True`` to grant the user permission.

.. warning::

    The object on which a permission is checked *is not verified*. That is, you could check the ``polls.vote_on_question`` permission on an instance of *any* random model and no warning would be given (checking validity would add unnecessary overhead to such a common operation). This is important because, if the instance provided does not define the appropriate object-level access methods (such as ``_user_can_vote_on_question()``), the permission is assumed to be *granted* at the object level, since :ref:`permissions default open <permissions-default>`.

Protecting views
----------------

Protecting views that should only be accessed by users with certain object-level permissions is supported by Djem's extensions of the standard Django ``permission_required`` decorator for function-based views and ``PermissionRequiredMixin`` mixin for class-based views.

See the Django documentation for `the decorator <https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permission-required-decorator>`_ and `the mixin <https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permissionrequiredmixin-mixin>`_ for the basic functionality these helpers provide.

Checking an object-level permission involves querying for an instance of the model the permission is for. If such an instance cannot be found, a ``Http404`` exception is raised.

.. versionadded:: 0.5
    The :func:`permission_required` decorator and the :class:`PermissionRequiredMixin` class-based view mixin.

Basic usage
~~~~~~~~~~~

Usage of Djem's :func:`permission_required` and :class:`PermissionRequiredMixin` is very similar to the originals except that specifying an object-level permission is done using a tuple of two strings: the first naming the permission, the second naming the view function keyword argument that contains the primary key of the object to test.

Model-level permissions can still be checked by specifying a plain string as per usual.

A mixture of multiple model-level and object-level permissions is also fully supported. In this case, permissions are checked in the order they are listed, and a user must pass every check in order to access the view.

.. code-block:: python

    from django.views import View
    from djem.auth import PermissionRequiredMixin, permission_required

    # Check a model-level permission on a function-based view
    @permission_required('polls.view_questions')
    def cast_vote(request, question):
        ...

    # Check an object-level permission on a function-based view
    @permission_required(('polls.vote_on_question', 'question'))
    def cast_vote(request, question):
        ...

    # Check a mixture of permissions on a function-based view
    @permission_required('polls.view_questions', ('polls.vote_on_question', 'question'))
    def cast_vote(request, question):
        ...

    # Check a model-level permission on a class-based view
    class CastVote(PermissionRequiredMixin, View):

        permission_required = 'polls.view_questions'
        ...

    # Check an object-level permission on a class-based view
    class CastVote(PermissionRequiredMixin, View):

        permission_required = [('polls.vote_on_question', 'question')]
        ...

    # Check a mixture of permissions on a class-based view
    class CastVote(PermissionRequiredMixin, View):

        permission_required = ['polls.view_questions', ('polls.vote_on_question', 'question')]
        ...

.. note::

    When specifying a single object-level permission using the ``permission_required`` attribute of :class:`PermissionRequiredMixin`, it must be given as an item of an iterable (e.g. a list). While a single model-level permission can be provided as either a plain string *or* a single-item iterable (a feature inherited from Django's own mixin class), because an object-level permission is defined in a tuple - which is itself an iterable - it would be treated as two model-level permissions (and would be invalid).

``PermissionRequiredMixin`` and the URLconf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Like all attributes of class-based views, the ``permission_required`` attribute added by :class:`PermissionRequiredMixin` can be specified/overridden in the URLconf:

.. code-block:: python

    from django.conf.urls import url
    from .views import CastVote

    urlpatterns = [
        url(
            r'^question/(?P<question>\d+)/votes/cast/$',
            CastVote.as_view(permission_required=['polls.view_questions', ('polls.vote_on_question', 'question')]),
            name='cast-vote'
        )
    ]

Controlling denied access
~~~~~~~~~~~~~~~~~~~~~~~~~

As with the originals, ``login_url`` and ``raise_exception`` are fully supported - as arguments to the :func:`permission_required` decorator or as attributes of a class inheriting from :class:`PermissionRequiredMixin`. These allow additional control over what happens when a user is denied access to a view protected by the decorator/mixin. See the `Django documentation for permission_required <https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permission-required-decorator>`_ for more info on how these features work.

Djem extends this control slightly with the :setting:`DJEM_DEFAULT_403` setting. This setting can be used to control the *default value* of ``raise_exception``. Django's default is to NOT raise the ``PermissionDenied`` exception, preferring to redirect to the login view, but allowing you to override this behaviour per-view using ``raise_exception``. Setting :setting:`DJEM_DEFAULT_403` to ``True`` allows you to configure all protected views to raise the ``PermissionDenied`` exception by default, while still allowing per-view customisation with ``raise_exception``.

Argument replacement
~~~~~~~~~~~~~~~~~~~~

When using either :func:`permission_required` or :class:`PermissionRequiredMixin` to protect a view using object-level permissions, and the user passes all permission checks, any arguments named in an object-level permission two-tuple will be replaced with the appropriate instances.

These instances will already have been queried in order to check the user's permissions against them, so they are injected into the view's keyword arguments, replacing those that specified the primary key used in the queries. This allows the view to access such instances without needing to query for them again.

In the "cast vote" view examples used above, the view accepts a ``question`` keyword argument. This argument is named as the source of the primary key of a ``Question`` record, and used to check the user's ``polls.vote_on_question`` permission against that specific ``Question``. While the view was originally passed the *primary key* of a ``Question`` (as controlled by the URLconf), this is used and replaced as part of the permissions check, and the view sees a ``Question`` *instance*.

Checking in templates
---------------------

Checking object-level permissions in a Django template can be done using the :ttag:`ifperm` and :ttag:`ifnotperm` template tags. These are block tags whose content is displayed if the permissions check passes. For :ttag:`ifperm`, it passes if the user *has* the permission. For :ttag:`ifnotperm`, it passes if the user *does not* have the permission. Each tag supports an ``else`` block, whose content is displayed if the permissions check fails.

Each tag must be passed a user instance, the name of the permission to check and the object to check it on.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% else %}
        You do not have permission to vote on this question.
    {% endifperm %}
    ...

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% else %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifnotperm %}
    ...

Checking via ``User`` instances
-------------------------------

The ``has_perm()`` method provided by Django's ``User`` model (or by ``PermissionsMixin`` if using a custom user model) accepts an optional ``obj`` argument. Django does nothing with it by default, but passing it will invoke Djem's object-level permissions system. Thus it can be used to check a user's object-level permissions on a given object.

Continuing with the modified ``Question`` model defined above:

.. code-block:: python

    >>> user = User.objects.get(username='alice')
    >>> question = Question.objects.filter(voters=user).first()
    >>> user.has_perm('polls.vote_on_question', question)
    True

    >>> question = Question.objects.exclude(voters=user).first()
    >>> user.has_perm('polls.vote_on_question', question)
    False

See ``has_perm()`` documentation for `User <https://docs.djangoproject.com/en/stable/ref/contrib/auth/#django.contrib.auth.models.User.has_perm>`_ and `PermissionsMixin <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#django.contrib.auth.models.PermissionsMixin.has_perm>`_.

.. note::

    In addition to ``has_perm()``, the ``has_perms()``, ``get_group_permissions()`` and ``get_all_permissions()`` methods on ``User``/``PermissionMixin`` also accept the optional ``obj`` argument and work with the object-level permissions system.


Caching
=======

Like ``ModelBackend`` `does for model-level permissions <https://docs.djangoproject.com/en/stable/topics/auth/default/#permission-caching>`_, the :class:`ObjectPermissionsBackend` caches object-level permissions on the ``User`` object after the first time they are checked. Unlike ``ModelBackend``, the user's entire set of object-level permissions are not determined and cached on this first access, only the specific permission being tested, for the specific object given.

This caching system has the same advantages and disadvantages as that used for model-level permissions. Multiple checks of the same permission (on the same object) in the same request will only need to execute the (possibly expensive) logic in your ``_user_can_<permission_name>()``/``_group_can_<permission_name>()`` methods once. However, that means that if something changes within the request that would alter the state of a permission, and that permission has already been checked, the ``User`` object will not immediately reflect the new state of the permission - a new instance of the ``User`` would need to be queried from the database. Exactly what *might* affect the state of a permission depends entirely upon the logic implemented in the ``_user_can_<permission_name>()``/``_group_can_<permission_name>()`` methods, so this is something to be aware of both while writing these methods and while using them.


Other ``PermissionsMixin`` methods
==================================

The object-level permissions system is fully compatible with Django's ``PermissionsMixin``, meaning it supports more than just the ``has_perm()`` method. Other supported methods include:

* ``has_perms()``: For checking multiple permissions against a ``User`` instance at once.
* ``get_all_permissions()``: To obtain a list of all permissions accessible to the user, either directly or via their groups, with all necessary object-level logic applied.
* ``get_group_permissions()``: To obtain a list of all permissions accessible to the user via their groups only, with all necessary object-level logic applied.

While ``has_perms()`` is a simple extension of ``has_perm()`` to allow checking multiple permissions at once, some care should be taken with ``get_all_permissions()`` and ``get_group_permissions()``.

Firstly, depending on the number of permissions your project uses, the amount that have object-level access methods defined, and the complexity of the logic used by those access methods, obtaining a list of available permissions could involve a lot of processing (compared to testing one at a time).

More subtly, ``get_group_permissions()`` can potentially list permissions that would not actually be granted to the user via a standard permissions checking. This is a side-effect of the fact that :ref:`object-level permissions default open <permissions-default>`. If a user-based object-level access method denied a certain permission, and no group-based access method was defined, a normal permissions check would return ``False``, on account of the user-based check. But a group-only check, such as performed by ``get_group_permissions()`` would *grant* the permission, due to there being no object-level access method to indicate otherwise.

While not accessible via ``PermissionsMixin``, :class:`ObjectPermissionsBackend` also contains a ``get_user_permissions()`` method which suffers from the same side-effect due to ignoring group-based access methods.
