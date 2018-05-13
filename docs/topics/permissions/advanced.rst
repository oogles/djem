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


.. _permissions-advanced-clear-cache:

Clearing the permission cache
=============================

As described in :ref:`permissions-cache`, the results of object-level permission checks are cached, which has the downside of the results potentially getting out-of-date if elements of the state used to determine the permission are changed.

By default, the only way to clear this cache is to re-query for a new user instance. This is particularly annoying if needing to replace the user instance on the ``request`` object. :class:`OLPMixin` provides a :meth:`~OLPMixin.clear_perm_cache` method, which, as the name suggests, clears the permissions cache on the user instance.

In addition to clearing the OLP cache, :meth:`~OLPMixin.clear_perm_cache` also clears Django's model-level permissions caches, for good measure.


.. _user-based-logging:

User-based logging
==================

:class:`OLPMixin` provides a series of methods for creating, storing, and retrieving user-based logs. These logs can be used for anything - recording events, detailing the steps taken by a complex process, etc. Each log is created with its own name, and can be later retrieved using that name. The logs themselves are maintained as Python lists - each item in the list being a separate entry, or line, in the log. This allows them to be easily appended to over time.

When a new log is created, it becomes the "active" log - the one to which new log entries are appended. There can only be one active log at a time. If another log is active when a new log is created, it gets pushed back in the queue, and will become active again when the new log is finished. Logs must be explicitly declared "finished" in order to both re-activate previous logs and also to enable retrieving the log (unfinished logs cannot be retrieved).

The logs are stored internally on the :class:`OLPMixin` instance - thus, the ``User`` instance. They will persist for the lifetime of that instance, typically a single request. No options for more persistent storage of these logs is included, but :ref:`it is possible <user-based-logging-persistence>`.

The methods available are:

* :meth:`~OLPMixin.start_log`: Create a new log with a given name, making it the active log.
* :meth:`~OLPMixin.log`: Add a new entry to the active log.
* :meth:`~OLPMixin.end_log`: Mark the active log as finished.
* :meth:`~OLPMixin.discard_log`: Remove the active log.
* :meth:`~OLPMixin.get_log`: Retrieve a log with the given name.
* :meth:`~OLPMixin.get_last_log`: Retrieve the most recently finished log.

By default, :meth:`~OLPMixin.get_log` and :meth:`~OLPMixin.get_last_log` retrieve logs as strings, but the internal lists can be retrieved by passing ``raw=True`` to either method.

As an example, consider a ``Product`` model, where a user may not be allowed to delete a product that is currently an actively-sold product line or if the product currently has any stock on hand. These restrictions can be imposed by an object-level access method, and a log can allow auditing why the permission was not granted:

.. code-block:: python

    from django.db import models

    from .inventory import get_quantity_in_stock


    class Product(models.Model):

        code = models.CharField(max_length=20)
        name = models.CharField(max_length=100)
        active = models.BooleanField(default=True)
        supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

        def _user_can_delete_product(self, user):

            user.start_log('delete-product-{0}'.format(self.pk))

            if self.active:
                user.log('Cannot delete active product lines')
                allowed = False
            elif get_quantity_in_stock(self):
                user.log('Cannot delete products with stock on hand')
                allowed = False
            else:
                user.log('Product can be deleted')
                allowed = True

            user.end_log()

            return allowed

Nested logs
-----------

As mentioned, if a log is already active and a new log is created, the new log becomes active and the previous log will be re-activated when the new log is finished. This allows for logs to be nested without worrying about interfering with other logs.

Continuing the above ``Product`` example, deletion may also require that the user has permission to manage the inventory from the supplier in question. Thus, checking the "delete_product" permission can trigger a "manage_supplier" permission check. If both permissions perform logging, those logs are nested, but neither need to do anything special to handle it:

.. code-block:: python

    from django.conf import settings
    from django.db import models

    from .inventory import get_quantity_in_stock


    class Supplier(models.Model):

        name = models.CharField(max_length=100)
        managers = models.ManyToManyField(settings.AUTH_USER_MODEL)

        def _user_can_manage_supplier(self, user):

            user.start_log('manage-supplier-{0}'.format(self.pk))

            if not self.managers.filter(pk=user.pk).exists():
                user.log('You do not have permission to manage the inventory of {0}'.format(self.name))
                allowed = False
            else:
                allowed = True

            user.end_log()

            return allowed

        class Meta:
            permissions = (
                ('manage_supplier', "Can manage inventory from this supplier")
            )


    class Product(models.Model):

        code = models.CharField(max_length=20)
        name = models.CharField(max_length=100)
        active = models.BooleanField(default=True)
        supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

        def _user_can_delete_product(self, user):

            user.start_log('delete-product-{0}'.format(self.pk))

            if self.active:
                user.log('Cannot delete active product lines')
                allowed = False
            elif get_quantity_in_stock(self):
                user.log('Cannot delete products with stock on hand')
                allowed = False
            elif not user.has_perm('inventory.manage_supplier', self.supplier):
                user.log('You do not have permission to manage the inventory of {0}'.format(self.supplier.name))
                allowed = False
            else:
                user.log('Product can be deleted')
                allowed = True

            user.end_log()

            return allowed

Of course, sometimes is *is* useful to explicitly handle nested logs. Instead of duplicating the same log entry in both the "manage_supplier" and "delete_product" access methods, "delete_product" can simply incorporate the log generated by "manage_supplier" into its own, using :meth:`~OLPMixin.get_last_log`:

.. code-block:: python

    def _user_can_delete_product(self, user):

        ...
        elif not user.has_perm('inventory.manage_supplier', self.supplier):
            inner_log = user.get_last_log(raw=True)
            user.log(*inner_log)
            allowed = False
        ...

.. _user-based-logging-names:

Duplicate names
---------------

Creating a new log with the same name as another *unfinished* log is not possible - it will raise a ``ValueError``. Therefore, it is important to use sufficiently informative names. The above nested logging example uses two logs named after the permission they are checking and the object they are checking it on. If they were both to use the same generic name, e.g. ``'perm-log'``, attempting to call one from within the other would fail.

However, it is perfectly valid to re-use a name after the log has been finished. Doing so will overwrite the previous log when the new one is finished. This allows the same process to be run multiple times within the lifetime of the ``User`` instance on which the logs are stored, without causing issues. But it is important to note that only one instance of the log will be kept - the last one that was finished.

.. _user-based-logging-persistence:

Persistence
-----------

As noted above, logs are stored on the :class:`OLPMixin` instance itself. In the typical scenario - where the ``User`` instance incorporating the :class:`OLPMixin` is the authenticated user attached to incoming requests - this limits the ability to retrieve logs to the same request that created them. While this is sufficient in many cases, a more persistent storage mechanism may be required in some.

This can be achieved by customising the ``User`` model that incorporates :class:`OLPMixin`. There are many different ways it can be implemented - the following uses a basic model to store the logs in the database once they have been completed:

.. code-block:: python

    from django.contrib.auth.models import AbstractUser
    from django.db import models

    from djem.auth import OLPMixin


    class UserLog(models.Model):

        name = models.CharField(max_length=100)
        log = models.TextField()


    class User(OLPMixin, AbstractUser):

        def end_log(self):

            name, log = super(User, self).end_log()

            UserLog.objects.create(
                name=name,
                log='\n'.join(log)
            )

            return name, log

Thread safety
-------------

Despite being able to be safely nested, user-based logging is not thread safe. Due to the way the "active" log is maintained, multiple threads sharing the same :class:`OLPMixin` instance can easily contaminate each other's logs. In addition, if they run the same process (which uses user-based logging), they may error out due to being unable to have :ref:`multiple unfinished logs with the same name <user-based-logging-names>`.

Multiple threads using *separate* instances of :class:`OLPMixin` will only be problematic if implementing some kind of :ref:`persistent storage <user-based-logging-persistence>` mechanism for the logs, depending on the nature of the chosen mechanism.

When using user-based logging as part of a standard request-response cycle, thread safety is not a concern as each request uses a separate ``User`` instance.

Automatically logging permission checks
---------------------------------------

:class:`OLPMixin` leverages user-based logging to support automatically logging all permission checks made via its overridden :meth:`~OLPMixin.has_perm` method - both model-level and object-level. There are multiple levels of logging available, controlled via the :setting:`DJEM_PERM_LOG_VERBOSITY` setting:

* ``0``: No automatic logging
* ``1``: Logs are automatically created for each permission check, with minimal automatic entries
* ``2``: Logs are automatically created for each permission check, with more informative automatic entries

Using a setting above ``0`` configures :meth:`~OLPMixin.has_perm` to create an appropriately-named log and populate it with several automated entries as appropriate (based on the verbosity level chosen). In addition to the automated entries, having a suitable log already created and active provides a simpler experience if utilising logging in object-level access methods. Revisiting the above "delete_product" access method, enabling automatic logging allows for a simpler method definition:

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

The output from a "delete_product" permission check with a :setting:`DJEM_PERM_LOG_VERBOSITY` setting of ``1`` might look something like:

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

Retrieving these automated logs via :meth:`~OLPMixin.get_log` requires knowing their name. The format used to name them is as follows:

For model-level permission checks: ``auto-<permission_name>``

For object-level permission checks: ``auto-<permission_name>-<object_id>``

E.g. ``auto-inventory.delete_permission``, ``auto-inventory.delete_permission-1375``
