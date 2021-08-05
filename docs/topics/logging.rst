======================
Instance-based Logging
======================

.. currentmodule:: djem.models

The :class:`Loggable` mixin provides a series of methods for creating, storing, and retrieving "instance-based" logs - that is, logs that are specific to an instance of a class incorporating :class:`Loggable`. These logs can be used for anything - recording events, detailing the steps taken by a complex process, etc. Each log is created with its own name, and can be later retrieved from the instance using that name. The logs themselves are maintained as Python lists - each item in the list being a separate entry, or line, in the log. This allows them to be easily appended to over time.

When a new log is created, it becomes the "active" log for that instance - the one to which new log entries are appended. There can only be one active log on an instance at a time. If another log is active when a new log is created, it gets pushed back in the queue, and will become active again when the new log is finished. Logs must be explicitly declared "finished" in order to both re-activate previous logs and also to enable retrieving the log (unfinished logs cannot be retrieved).

The logs are stored internally on the instance. They will persist for the lifetime of that instance. No support for more persistent storage of these logs is included, but :ref:`it is possible <instance-based-logging-persistence>`.

The methods available are:

* :meth:`~Loggable.start_log`: Create a new log with a given name, making it the active log.
* :meth:`~Loggable.log`: Add a new entry to the active log.
* :meth:`~Loggable.end_log`: Mark the active log as finished.
* :meth:`~Loggable.discard_log`: Remove the active log.
* :meth:`~Loggable.get_log`: Retrieve a log with the given name.
* :meth:`~Loggable.get_last_log`: Retrieve the most recently finished log.

By default, :meth:`~Loggable.get_log` and :meth:`~Loggable.get_last_log` retrieve logs as strings, but copies of the internal lists can be retrieved by passing ``raw=True`` to either method.

:class:`OLPMixin`, used to provide advanced features to Djem's :doc:`object-level permissions system <permissions/index>`, inherits from :class:`Loggable`. Keeping user-based logs of permission checks is the primary use of instance-based logging. The examples in this documentation use user-based logging in object-level permission access methods to illustrate the supported features of :class:`Loggable`. While :class:`OLPMixin` provides support for :ref:`automatically logging permission checks <permissions-advanced-logging>`, these examples assume that feature is disabled and demonstrate the basic functionality of the system.

Consider a ``Product`` model where a user may not be allowed to delete a product that is currently an actively-sold product line or if the product currently has any stock on hand. These restrictions can be imposed by an object-level access method, and a log can allow auditing why the permission was not granted:

.. code-block:: python

    from django.db import models

    from .utils import get_quantity_in_stock


    class Product(models.Model):

        code = models.CharField(max_length=20)
        name = models.CharField(max_length=100)
        active = models.BooleanField(default=True)

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


.. _instance-based-logging-nesting:

Nested logs
===========

As mentioned, if a log is already active and a new log is created, the new log becomes active and the previous log will be *reactivated* when the new log is finished. This allows for logs to be nested without worrying about interfering with other logs.

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

Of course, sometimes it *is* useful to explicitly handle nested logs. Instead of duplicating the same log entry in both the "manage_supplier" and "delete_product" access methods, "delete_product" can simply incorporate the log generated by "manage_supplier" into its own, using :meth:`~Loggable.get_last_log`:

.. code-block:: python

    def _user_can_delete_product(self, user):

        ...
        elif not user.has_perm('inventory.manage_supplier', self.supplier):
            inner_log = user.get_last_log(raw=True)
            user.log(*inner_log)
            allowed = False
        ...


.. _instance-based-logging-names:

Duplicate names
===============

Creating a new log with the same name as another *unfinished* log is not possible - it will raise a ``ValueError``. Therefore, it is important to use sufficiently informative names. The above nested logging example uses two logs named after the permission they are checking and the object they are checking it on. If they were both to use the same generic name, e.g. ``'perm-log'``, attempting to call one from within the other would fail.

However, it is perfectly valid to re-use a name after the log has been finished. Doing so will overwrite the previous log when the new one is finished. This allows the same process to be run multiple times within the lifetime of the :class:`Loggable` instance, without causing issues. But it is important to note that only the latest version of the log will be kept.


.. _instance-based-logging-persistence:

Persistence
===========

As noted above, logs are stored on the :class:`Loggable` instance itself. This can influence the types of classes that it makes sense to incorporate :class:`Loggable` into. It may not be useful to use the mixin on classes that generate short-lived or difficult-to-access instances.

A custom user model is a good choice to add :class:`Loggable` to (or, even better, :class:`OLPMixin`). In the typical scenario, a user instance is accessible on every incoming request, can easily (and is often required to) be passed around among various function/method calls, and persists for the entire request-response cycle.

If there is a need for a more persistent storage mechanism for these logs, there are a number of ways that can be achieved. One possible solution is to override a suitable method from :class:`Loggable`. The following example uses a simple model to store logs made on a custom ``User`` model once they have been completed:

.. code-block:: python

    from django.contrib.auth.models import AbstractUser
    from django.db import models

    from djem.models import Loggable


    class UserLog(models.Model):

        name = models.CharField(max_length=100)
        log = models.TextField()


    class User(Loggable, AbstractUser):

        def end_log(self):

            name, log = super(User, self).end_log()

            UserLog.objects.create(
                name=name,
                log='\n'.join(log)
            )

            return name, log


Thread safety
=============

Despite being able to be :ref:`safely nested <instance-based-logging-nesting>`, instance-based logging is not thread safe. Due to the way the "active" log is maintained, multiple threads sharing the same :class:`Loggable` instance can easily contaminate each other's logs. In addition, if they run the same process (that uses instance-based logging), they may error out due to being unable to have :ref:`multiple unfinished logs with the same name <instance-based-logging-names>`.

Multiple threads using *separate* instances of :class:`Loggable` will only be problematic if implementing some kind of :ref:`persistent storage <instance-based-logging-persistence>` mechanism for the logs, depending on the nature of the chosen mechanism.

When using :class:`Loggable` (or :class:`OLPMixin`) on a custom user model, as part of a standard request-response cycle, thread safety is not a concern as each request uses a separate user instance.
