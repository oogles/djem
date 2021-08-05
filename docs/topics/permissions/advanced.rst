=================
Advanced Features
=================

.. currentmodule:: djem.models

Basic use of Djem's OLP system is a simple drop-in extension of Django's own permissions system, enabled by :class:`~djem.auth.ObjectPermissionsBackend`. If your user model, no matter how it is defined, is compatible with Django's default permissions system, it will be compatible with the OLP system as well.

However, more advanced features are available that require a higher level of configuration. Specifically, they *require* a custom user model - they will not be available if simply making use of Django's included ``auth.User`` model. Django `recommends using <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project>`_ a custom user model anyway (for new projects, at least), even if it doesn't actually customise anything.

To enable these advanced features, described below, your custom user model must include the :class:`OLPMixin`.

If not looking to actually customise anything, a custom user model incorporating :class:`OLPMixin` is as simple as:

.. code-block:: python

    from django.contrib.auth.models import AbstractUser

    from djem.models import OLPMixin


    class User(OLPMixin, AbstractUser):

        pass

If looking to customise the user model more heavily (for example, using an email address instead of a username as the user's identification token), use something like the following:

.. code-block:: python

    from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

    from djem.models import OLPMixin


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


.. _permissions-advanced-clear-cache:

Clearing the permission cache
=============================

As described in :ref:`permissions-cache`, the results of object-level permission checks are cached, which has the downside of the results potentially getting out-of-date if elements of the state used to determine the permission are changed.

By default, the only way to clear this cache is to re-query for a new user instance. This is particularly annoying if needing to replace the user instance on the ``request`` object. :class:`OLPMixin` provides a :meth:`~OLPMixin.clear_perm_cache` method, which, as the name suggests, clears the permissions cache on the user instance.

In addition to clearing the OLP cache, :meth:`~OLPMixin.clear_perm_cache` also clears Django's model-level permissions caches, for good measure.


.. _permissions-advanced-logging:

Automatically logging permission checks
=======================================

:class:`OLPMixin` leverages instance-based logging to support automatically logging all permission checks made via its overridden :meth:`~OLPMixin.has_perm` method - both model-level and object-level.

Read the :doc:`documentation for the instance-based logging functionality <../logging>` provided by :class:`Loggable` for an introduction to the system. :class:`OLPMixin` inherits from :class:`Loggable`, and thus offers all the same features, in addition to those specific to permissions.

There are multiple levels of automatic permission logging available, controlled via the :setting:`DJEM_PERM_LOG_VERBOSITY` setting:

* ``0``: No automatic logging
* ``1``: Logs are automatically created for each permission check, with minimal automatic entries
* ``2``: Logs are automatically created for each permission check, with more informative automatic entries

Using a setting above ``0`` configures :meth:`~OLPMixin.has_perm` to create an appropriately-named log and populate it with automated entries as appropriate (based on the verbosity level chosen). In addition to the automated entries, having a suitable log already created and active provides a simpler experience if utilising logging in object-level access methods. Revisiting the "delete_product" access method described in the :doc:`instance-based logging examples <../logging>`, enabling automatic logging allows for a simpler method definition:

.. code-block:: python

    class Product(models.Model):

        code = models.CharField(max_length=20)
        name = models.CharField(max_length=100)
        active = models.BooleanField(default=True)
        supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

        def _user_can_delete_product(self, user):

            if self.active:
                user.log('Cannot delete active product lines')
                return False
            elif get_quantity_in_stock(self):
                user.log('Cannot delete products with stock on hand')
                return False
            elif not user.has_perm('inventory.manage_supplier', self.supplier):
                inner_log = user.get_last_log(raw=True)
                user.log(*inner_log)
                return False

            user.log('Product can be deleted')
            return True

Log output
----------

Using the "delete_product" permission from the above ``Product`` model as a reference, the output of a permission check with a :setting:`DJEM_PERM_LOG_VERBOSITY` setting of ``1`` might look something like:

.. code-block:: text

    Model-level Result: Granted

    Cannot delete active product lines

    RESULT: Permission Denied

And with a :setting:`DJEM_PERM_LOG_VERBOSITY` of ``2``:

.. code-block:: text

    Permission: inventory.delete_product
    User: user.name (54)
    Object: PROD123 (1375)

    Model-level Result: Granted

    Cannot delete active product lines

    RESULT: Permission Denied

Log names
---------

Retrieving automatically generated permission logs via :meth:`~Loggable.get_log` requires knowing their name. As long as you know the name of the permission that was checked, and the primary key of the object it was checked against (where applicable), the name of the log can be easily determined:

For model-level permission checks: ``auto-<permission_name>`` (e.g. ``auto-inventory.delete_product``)

For object-level permission checks: ``auto-<permission_name>-<object_id>`` (e.g. ``auto-inventory.delete_product-1375``)
