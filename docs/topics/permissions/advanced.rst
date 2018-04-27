=================
Advanced Features
=================

.. currentmodule:: djem.auth

Basic use of Djem's OLP system is a simple drop-in extension of Django's own permissions system, enabled by :class:`ObjectPermissionsBackend`. If your user model, no matter how it is defined, is compatible with Django's default permissions system, it will be compatible with the OLP system as well.

However, more advanced features are available that require a higher level of configuration. Specifically, they *require* a custom user model - they will not be available if simply making use of Django's included ``auth.User`` model. Django `recommends using <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project>`_ a custom user model anyway (for new projects, at least), even if it doesn't actually customise anything.

To enable these advanced features, described below, your custom user model must include the :class:`OLPMixin`.

If not looking to actually customise anything, a custom user model incorporating :class:`OLPMixin` is as simple as:

.. code-block:: python

    from django.contrib.auth.models import AbstractUser

    from djem.auth import OLPMixin


    class User(OLPMixin, AbstractUser):

        pass

If looking to customise the user model more heavily (for example, using an email address instead of a username as the user's identification token), use something like the following:

.. code-block:: python

    from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

    from djem.auth import OLPMixin


    class User(OLPMixin, AbstractBaseUser, PermissionsMixin):

        ...

.. versionadded:: 0.7
    :class:`OLPMixin`

.. important::

    :class:`OLPMixin` must be listed *ahead* of ``AbstractUser``/``PermissionsMixin`` in order for it to work correctly.


Superusers
==========

The Django permissions system automatically grants any and all permissions to a ``User`` instance with the ``is_superuser`` flag set to ``True``. By default, this is how the OLP system operates as well: no object-level access methods are executed, the superuser is simply granted the permission.

There are, however, situations in which this is not desirable. For example, you may want to define a model that does not grant the "delete" permission to anyone but the user that created it, no matter how "super" the user is. It would be trivial to configure the model to achieve this for a standard user, but a superuser would bypass any custom object-level access methods and be granted the permission anyway.

Djem provides a means of forcing superusers to be subject to the same OLP logic as regular users. They are still implicitly granted all permissions at the model level, but any object-level access methods *will* be executed and *can* deny the user permission.

In order to enable this feature, two things are required:

* A custom user model including :class:`OLPMixin`, as described above.
* The :setting:`DJEM_UNIVERSAL_OLP` setting set to ``True``.

With these two requirements met, object-level permissions will be applied "universally", including for superusers.

.. note::

    Enabling this feature will cause superusers to be subject to the OLP logic for *all* permissions that define some. If your project contains permissions which should still be granted to superusers regardless of the additional checks that standard users are subject to, the relevant access method can include a simple guard clause:

    .. code-block:: python

        def _user_can_vote_on_question(self, user):

            if user.is_superuser:
                return True

            # Do custom logic
            ...
