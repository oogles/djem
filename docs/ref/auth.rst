====
Auth
====

.. module:: djem.auth

``ObjectPermissionsBackend``
============================

.. class:: ObjectPermissionsBackend

    A custom Django authentication backend providing support for object-level permissions.

    Does not provide any additional mechanisms for authentication, only authorisation.

    To use, list in the Django ``AUTHENTICATION_BACKENDS`` setting:

    .. code-block:: python

        AUTHENTICATION_BACKENDS = [
            'django.contrib.auth.backends.ModelBackend',
            'djem.auth.ObjectPermissionsBackend'
        ]


``permission_required``
=======================

.. function:: permission_required(*perms, login_url=None, raise_exception=settings.DJEM_DEFAULT_403)

    .. versionadded:: 0.5

    A replacement for Django's own ``permission_required`` decorator that adds support for object-level permissions.

    Object-level permissions are specified as a tuple of two strings: the first naming the permission, the second naming the view function keyword argument that contains the primary key of the object to test.

    E.g. Specifying one standard (model-level) and one object-level permission:

    .. code-block:: python

        from djem.auth import permission_required

        @permission_required('polls.view_questions', ('polls.vote_on_question', 'question'))
        def cast_vote(request, question):
            ...

    Checking the permission involves querying for an instance of the model the permission is for, using the primary key specified in the named argument. If such an instance cannot be found, a ``Http404`` exception is raised. If an instance *is* found, and the user has the appropriate permission, the primary key argument is *replaced* with the instance. This allows the view access to the instance without needing to query for it again.

    In the example above, ``question`` argument as seen by the view will be a ``Question`` instance, not the primary key as was originally passed to the function.

    Behaviour of the ``login_url`` and ``raise_exception`` keyword arguments is as per the original, except that the default value for ``raise_exception`` can be specified with the :setting:`DJEM_DEFAULT_403` setting.


``PermissionRequiredMixin``
===========================

.. class:: PermissionRequiredMixin

    .. versionadded:: 0.5

    A replacement for Django's own ``PermissionRequiredMixin`` class-based view mixin that adds support for object-level permissions.

    Object-level permissions are specified as a tuple of two strings: the first naming the permission, the second naming the view function keyword argument that contains the primary key of the object to test.

    The permission/s can be specified as an attribute of the view class, or via the URLconf.

    E.g. Specifying one standard (model-level) and one object-level permission as an attribute of the class:

    .. code-block:: python

        # views.py
        from django.views import View
        from djem.auth import PermissionRequiredMixin

        class CastVote(PermissionRequiredMixin, View):

            permission_required = ['polls.view_questions', ('polls.vote_on_question', 'question')]
            ...

    E.g. Specifying one standard (model-level) and one object-level permission via the URLconf:

    .. code-block:: python

        # urls.py
        from django.conf.urls import url
        from .views import CastVote

        urlpatterns = [
            url(
                r'^question/(?P<question>\d+)/votes/cast/$',
                CastVote.as_view(permission_required=['polls.view_questions', ('polls.vote_on_question', 'question')]),
                name='cast-vote'
            )
        ]

    As with Django's version, the ``permission_required`` attribute can be specified as a single permission or a sequence of permissions. When specifying only a single permission, only model-level permissions (i.e. a string) are valid - object-level permissions (i.e. a two-tuple) are not. Object-level permissions must always be provided as an item of an iterable.

    .. code-block:: python

        class CastVote(PermissionRequiredMixin, View):

            # Valid
            permission_required = 'polls.view_questions'

            # Valid
            permission_required = ['polls.view_questions', 'polls.vote_on_question']

            # Valid
            permission_required = ['polls.view_questions', ('polls.vote_on_question', 'question')]

            # INVALID
            permission_required = ('polls.vote_on_question', 'question')

    Checking the permission involves querying for an instance of the model the permission is for, using the primary key specified in the named argument. If such an instance cannot be found, a ``Http404`` exception is raised. If an instance *is* found, and the user has the appropriate permission, the primary key argument is *replaced* with the instance. This allows the view access to the instance without needing to query for it again.

    In the examples above, ``question`` argument as seen by the view will be a ``Question`` instance, not the primary key as was originally passed to the function.

    Behaviour of the ``login_url`` and ``raise_exception`` attributes is as per the original, except that the default value for ``raise_exception`` can be specified with the :setting:`DJEM_DEFAULT_403` setting.
