====================
Checking Permissions
====================

.. currentmodule:: djem.auth

The main ways of using the OLP system to check a user's permissions on a specific object are:

* the ``permission_required`` decorator for function-based views or ``PermissionRequiredMixin`` mixin for class-based views
* the ``ifperm`` and ``ifnotperm`` template tags
* the ``has_perm()`` method on a ``User`` instance

All of these approaches use the standard Django permissions system and rely on the custom :class:`ObjectPermissionsBackend` to call the appropriate object-level access methods. In the examples below, each permission check will result in ``_user_can_<permission_name>`` being called and provided the ``User`` instance involved in the check, and ``_group_can_<permission_name>`` being called and provided with a queryset of all ``Groups`` to which that user belongs. Either method can return ``True`` to grant the user permission.

.. warning::

    The object on which a permission is checked *is not verified*. That is, you could check the ``polls.vote_on_question`` permission on an instance of *any* random model and no warning would be given (checking validity would add unnecessary overhead to such a common operation). This is important because, if the instance provided does not define the appropriate object-level access methods, the permission is assumed to be *granted* at the object level, since :ref:`permissions default open <permissions-default>`.

Many of the below examples draw on the sample ``polls.Question`` model introduced in the :ref:`documentation on defining access methods<permissions-defining>`:

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


Protecting views
================

Protecting views that should only be accessed by users with certain object-level permissions is supported by Djem's extensions of the standard Django ``permission_required`` decorator (for function-based views) and ``PermissionRequiredMixin`` mixin (for class-based views).

See the Django documentation for `the decorator <https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permission-required-decorator>`_ and `the mixin <https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permissionrequiredmixin-mixin>`_ for the basic functionality these helpers provide.

Checking an object-level permission involves querying for an instance of the model the permission is for. If such an instance cannot be found, a ``Http404`` exception is raised.

.. versionadded:: 0.5
    The :func:`permission_required` decorator and the :class:`PermissionRequiredMixin` class-based view mixin.

Basic usage
-----------

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

    When specifying a single object-level permission using the ``permission_required`` attribute of :class:`PermissionRequiredMixin`, it must be given as an item of a sequence (e.g. a list). While a single model-level permission can be provided as either a plain string *or* a single-item sequence (a feature inherited from Django's own mixin class), because an object-level permission is defined in a tuple - which is itself an sequence - it would be treated as two model-level permissions (and would be invalid).

``PermissionRequiredMixin`` and the URLconf
-------------------------------------------

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
-------------------------

As with the originals, ``login_url`` and ``raise_exception`` are fully supported - as arguments to the :func:`permission_required` decorator or as attributes of a class inheriting from :class:`PermissionRequiredMixin`. These allow additional control over what happens when a user is denied access to a view protected by the decorator/mixin. See the `Django documentation for permission_required <https://docs.djangoproject.com/en/stable/topics/auth/default/#the-permission-required-decorator>`_ for more info on how these features work.

Djem extends this control slightly with the :setting:`DJEM_DEFAULT_403` setting. This setting can be used to control the *default value* of ``raise_exception``. Django's default is to NOT raise the ``PermissionDenied`` exception, preferring to redirect to the login view, but allowing you to override this behaviour per-view using ``raise_exception``. Setting :setting:`DJEM_DEFAULT_403` to ``True`` allows you to configure all protected views to raise the ``PermissionDenied`` exception by default, while still allowing per-view customisation with ``raise_exception``.

Argument replacement
--------------------

When using either :func:`permission_required` or :class:`PermissionRequiredMixin` to protect a view using object-level permissions, and the user passes all permission checks, any arguments named in an OLP two-tuple will be replaced with the appropriate instances.

These instances will already have been queried in order to check the user's permissions against them, so they are injected into the view's keyword arguments, replacing those that specified the primary key used in the queries. This allows the view to access such instances without needing to query for them again.

In the "cast vote" view examples used above, the view accepts a ``question`` keyword argument. This argument is named as the source of the primary key of a ``Question`` record, and used to check the user's ``polls.vote_on_question`` permission against that specific ``Question``. While the view was originally passed the *primary key* of a ``Question`` (as controlled by the URLconf), this is used and replaced as part of the permissions check, and the view sees a ``Question`` *instance*.


Checking in templates
=====================

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
===============================

The ``has_perm()`` method provided by Django's ``User`` model (or by ``PermissionsMixin`` if using a custom user model) accepts an optional ``obj`` argument. Django does nothing with it by default, but passing it will invoke Djem's OLP system. Thus it can be used to check a user's object-level permissions on a given object.

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

Other ``PermissionsMixin`` methods
----------------------------------

The OLP system is fully compatible with Django's ``PermissionsMixin``, meaning it supports more than just the ``has_perm()`` method. Other supported methods include:

* ``has_perms()``: For checking multiple permissions against a particular object at once.
* ``get_all_permissions()``: To obtain a list of all permissions accessible to the user, either directly or via their groups, with all necessary object-level logic applied.
* ``get_group_permissions()``: To obtain a list of all permissions accessible to the user via their groups only, with all necessary object-level logic applied.

While ``has_perms()`` is a simple extension of ``has_perm()`` to allow checking multiple permissions at once, some care should be taken with ``get_all_permissions()`` and ``get_group_permissions()``.

Firstly, depending on the number of permissions your project uses, the amount that have object-level access methods defined, and the complexity of the logic used by those access methods, obtaining a list of available permissions could involve a lot of processing (compared to testing one at a time).

More subtly, ``get_group_permissions()`` can potentially list permissions that would not actually be granted to the user via a standard permissions checking. This is a side-effect of the fact that :ref:`object-level permissions default open <permissions-default>`. If a user-based object-level access method denied a certain permission, and no group-based access method was defined, a normal permissions check would return ``False``, on account of the user-based check. But a group-only check, such as performed by ``get_group_permissions()`` would *grant* the permission, due to there being no object-level access method to indicate otherwise.

While not accessible via ``PermissionsMixin``, :class:`ObjectPermissionsBackend` also contains a ``get_user_permissions()`` method which suffers from the same side-effect due to ignoring group-based access methods.


.. _permissions-cache:

Caching
=======

Like ``ModelBackend`` `does for model-level permissions <https://docs.djangoproject.com/en/stable/topics/auth/default/#permission-caching>`_, :class:`ObjectPermissionsBackend` caches object-level permissions on the ``User`` object after the first time they are checked. Unlike ``ModelBackend``, the user's entire set of object-level permissions are not determined and cached on this first access, only the specific permission being tested, for the specific object given.

This caching system has the same advantages and disadvantages as that used at the model level. Multiple checks of the same permission (on the same object) in the same request will only need to execute the (possibly expensive) logic in your object-level access methods once. However, that means that if something changes within the request that would alter the state of a permission, and that permission has already been checked, the ``User`` object will not immediately reflect the new state of the permission. Exactly what *might* affect the state of a permission depends entirely upon the logic implemented in the ``_user_can_<permission_name>()``/``_group_can_<permission_name>()`` methods, so this is something to be aware of both while writing these methods and while using them.

Clearing the cache is possible by querying for a new instance of the ``User`` or, depending on how your user model is configured, :ref:`using the cache-clearing helper method <permissions-advanced-clear-cache>`.
