import re
import warnings
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import _user_has_perm
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

try:
    from django.db.models.utils import resolve_callables
except ImportError:  # pragma: no cover
    # Backport resolve_callables from Django 3.1+
    # TODO: Remove once Django 3.1+ becomes the minimum supported version
    def resolve_callables(mapping):
        for k, v in mapping.items():
            yield k, v() if callable(v) else v

from djem.auth import get_user_log_verbosity
from djem.exceptions import ModelAmbiguousVersionError

whitespace_regex = re.compile(r'\W+')

__all__ = (
    'Loggable', 'OLPMixin', 'MixableQuerySet',
    'Auditable', 'AuditableQuerySet', 'CommonInfoMixin', 'CommonInfoQuerySet',
    'Archivable', 'ArchivableQuerySet', 'ArchivableMixin',
    'Versionable', 'VersionableQuerySet', 'VersioningMixin', 'VersioningQuerySet',
    'StaticAbstract', 'StaticAbstractQuerySet',
)


class Loggable:
    """
    A mixin for creating, storing, and retrieving logs on an instance. Named
    logs are stored internally on the ``Loggable`` instance and persist for the
    lifetime of the object. A single log is "active" at any given time and can
    be freely appended to while it is.
    """
    
    def __init__(self, *args, **kwargs):
        
        self._active_logs = OrderedDict()
        self._finished_logs = OrderedDict()
        
        super().__init__(*args, **kwargs)
    
    def start_log(self, name):
        """
        Start a new log with the given ``name``. The new log becomes the
        current "active" log. Queue any previous active log so that it can be
        reactivated when the new log is either finished or discarded.
        
        :param name: The name of the log.
        """
        
        if name in self._active_logs:
            raise ValueError('A log named "{0}" is already active.'.format(name))
        
        self._active_logs[name] = []
    
    def end_log(self):
        """
        End the currently active log and return a ``(name, log)`` tuple, where
        ``name`` is the name of the log that was ended and ``log`` is a list of
        the entries that have been added to the log. Reactivate the previous
        log, if any.
        
        The returned list will be a *copy* of the one used to store the log
        internally, allowing it to be safely manipulated without affecting the
        original log.
        
        A log must be ended in order to be retrieved.
        
        :return: A ``(name, log)`` tuple.
        """
        
        # Pop from active logs to move to finished logs
        try:
            name, log = self._active_logs.popitem()
        except KeyError:
            raise KeyError('No active log to finish.')
        
        # If a log with the same name has been finished previously, remove it
        # from the finished logs dict before adding this one, so that this one
        # is added to the "end" of the ordered dict.
        if name in self._finished_logs:
            self._finished_logs.pop(name)
        
        self._finished_logs[name] = log
        
        return name, log
    
    def discard_log(self):
        """
        Discard the currently active log. Reactivate the previous log, if any.
        """
        
        try:
            self._active_logs.popitem()
        except KeyError:
            raise KeyError('No active log to discard.')
    
    def log(self, *lines):
        """
        Append to the currently active log. Each given argument will be added
        as a separate line to the log.
        
        :param lines: Individual lines to add to the log.
        """
        
        # Pop to get the last item
        try:
            name, log = self._active_logs.popitem()
        except KeyError:
            raise KeyError('No active log to append to. Has one been started?')
        
        # Append to the log
        log.extend(lines)
        
        # Put back in the active logs dict
        self._active_logs[name] = log
    
    def get_log(self, name, raw=False):
        """
        Return the named log, as a string. The log must have been ended (via
        ``end_log()``) in order to retrieve it.
        
        Return a raw list of lines in the log if ``raw=True``. In this case,
        the returned list will be a *copy* of the one used to store the log
        internally, allowing it to be safely manipulated without affecting the
        original log.
        
        :param name: The name of the log to retrieve.
        :param raw: ``True`` to return the log as a list. Returned as a string by default.
        :return: The log, either as a string or a list.
        """
        
        try:
            log = self._finished_logs[name]
        except KeyError:
            raise KeyError('No log found for "{0}". Has it been finished?'.format(name))
        
        if raw:
            return list(log)  # return a copy
        
        return '\n'.join(log)
    
    def get_last_log(self, raw=False):
        """
        Return the most recently finished log, as a string.
        
        Return a raw list of lines in the log if ``raw=True``. In this case,
        the returned list will be a *copy* of the one used to store the log
        internally, allowing it to be safely manipulated without affecting the
        original log.
        
        :param raw: ``True`` to return the log as a list. Returned as a string by default.
        :return: The log, either as a string or a list.
        """
        
        # Pop to get the last item, but put it straight back
        try:
            name, log = self._finished_logs.popitem()
        except KeyError:
            raise KeyError('No finished logs to retrieve.')
        
        self._finished_logs[name] = log
        
        if raw:
            return list(log)  # return a copy
        
        return '\n'.join(log)


class OLPMixin(Loggable):
    """
    A companion to Django's ``PermissionsMixin`` that enables additional
    advanced features of the object-level permission system. It is not
    necessary to use this mixin in order to use object-level permissions,
    it just provides additional functionality (such as logging permission
    checks, optionally allowing superusers to be restricted by object-level
    conditions, etc).
    """
    
    #
    # NOTE: This does not *extend* `PermissionsMixin` so that it can be
    # used along with Django's `AbstractUser`, which already includes
    # `PermissionsMixin`.
    #
    
    def __init__(self, *args, **kwargs):
        
        self._olp_cache = {}
        
        super().__init__(*args, **kwargs)
    
    def _check_perm(self, perm, obj):
        
        if not getattr(settings, 'DJEM_UNIVERSAL_OLP', False):
            # Default behaviour: active superusers implicitly have ALL permissions
            if self.is_active and self.is_superuser:
                return True, 'Active superuser: Implicit permission'
            
            return _user_has_perm(self, perm, obj), None
        else:
            # "Universal OLP" behaviour: active superusers implicitly have all
            # permissions at the model level, but are subject to object-level
            # checks
            if not obj and self.is_active and self.is_superuser:
                return True, 'Active superuser: Implicit permission (model-level)'
            
            return _user_has_perm(self, perm, obj), None
    
    def logged_has_perm(self, perm, obj=None, verbosity=1):
        
        log_key = 'auto-{}'.format(perm)
        if obj:
            log_key = '{}-{}'.format(log_key, obj.pk)

        self.start_log(log_key)
        
        if verbosity > 1:
            perm_log = 'Permission: {}'.format(perm)
            user_log = 'User: {} ({})'.format(self.get_username(), self.pk)
            
            if obj:
                self.log(perm_log, user_log, 'Object: {} ({})\n'.format(str(obj), obj.pk))
            else:
                user_log = '{}\n'.format(user_log)
                self.log(perm_log, user_log)
        
        has_perm, log_entry = self._check_perm(perm, obj)
        
        if log_entry:
            self.log(log_entry)
        
        self.log('\nRESULT: {}'.format('Permission Granted' if has_perm else 'Permission Denied'))
        self.end_log()
        
        return has_perm
    
    def has_perm(self, perm, obj=None):
        
        verbosity = get_user_log_verbosity()
        
        if verbosity:
            return self.logged_has_perm(perm, obj, verbosity)
        else:
            has_perm, log_entry = self._check_perm(perm, obj)
            return has_perm
    
    def clear_perm_cache(self):
        """
        Clear the object-level and model-level permissions caches on the user
        instance.
        """
        
        # Clear the object-level permissions cache
        self._olp_cache = {}
        
        # Clear the model-level permissions cache as well, for good measure
        try:
            del self._user_perm_cache
            del self._group_perm_cache
            del self._perm_cache
        except AttributeError:
            pass


class MixableQuerySet:
    """
    A mixin for ``QuerySet`` classes that simply provides an enhanced
    :meth:`~MixableQuerySet.as_manager` method that can be used to combine
    the queryset class with any number of other queryset classes automatically.
    """
    
    @classmethod
    def as_manager(cls, *other_querysets):
        """
        Similar to the ``as_manager`` classmethod `available on regular Django
        queryset classes
        <https://docs.djangoproject.com/en/stable/topics/db/managers/#creating-a-manager-with-queryset-methods>`_,
        this returns an instance of ``Manager`` with a copy of the queryset's
        methods. However, it also accepts *other* queryset classes as arguments
        and includes *their* methods in the created ``Manager`` also. This
        allows easily creating combinations of this queryset class with other
        custom queryset classes, without needing to manually create an extra
        class to do the grouping.
        
        This is only useful where the querysets being combined do not contain
        conflicting methods. Method inheritance is supported (i.e. multiple
        querysets can contain the same method and they will be resolved in
        normal method resolution order), but depending on the logic of those
        methods, they may not be compatible. In such cases, an extra class
        resolving any incompatibilities is still required.
        """
        
        #
        # Mostly copied from Django's QuerySet.as_manager(), but extended to
        # support combining querysets
        #
        
        queryset = cls
        base_name = cls.__name__
        
        # Slice "queryset" off the end of the base name if found. This just
        # makes the name a little nicer (and shorter) in common cases.
        if base_name.lower().endswith('queryset'):
            base_name = base_name[:-8]
        
        if other_querysets:
            # Create a single QuerySet that combines all given queryset classes
            base_name = f'{base_name}AndFriends'
            queryset = type(f'{base_name}QuerySet', (cls, *other_querysets), {})
        
        manager = models.Manager.from_queryset(queryset, f'{base_name}Manager')()
        manager._built_with_as_manager = True
        
        return manager
    as_manager.queryset_only = True


class AuditableQuerySet(MixableQuerySet, models.QuerySet):
    """
    Provides custom functionality pertaining to the fields provided by
    :class:`Auditable`.
    """
    
    def create(self, _user=None, **kwargs):
        """
        Overridden to ensure a user is provided to the ``save()`` call on the
        model instance. The ``_user`` argument (named to reduce potential
        conflicts with model field names) is the user instance to pass through.
        It is required unless the :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE`
        setting is ``False``.
        """
        
        # TODO: Remove fallback setting in 1.0
        require_user = getattr(
            settings,
            'DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE',
            getattr(settings, 'DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE', True)  # backwards compat.
        )
        if require_user and not _user:
            raise TypeError('create() requires the first positional argument to be a user model instance.')
        
        #
        # The below is copied from QuerySet.create() (as at Django 3.2.6) and
        # changed to pass the `user` argument to save()
        #
        
        obj = self.model(**kwargs)
        
        self._for_write = True
        obj.save(_user, force_insert=True, using=self.db)
        
        return obj
    
    def _extract_model_params(self, defaults, **kwargs):
        
        # Used by get_or_create() to combine `defaults` and `kwargs` to form
        # the params used by create(). Performs validation on fields, which
        # the injected `_user` param fails. So pop `_user` from `defaults`
        # before calling super(), and add it back afterwards.
        
        user = defaults.pop('_user')
        params = super()._extract_model_params(defaults, **kwargs)
        
        params['_user'] = user
        
        return params
    
    def get_or_create(self, defaults=None, _user=None, **kwargs):
        """
        Overridden to ensure a user is provided to the ``save()`` call on the
        model instance, if a record needs to be created. The ``_user`` argument
        (named to reduce potential conflicts with model field names) is the
        user instance to pass through. It is required unless the
        :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` setting is ``False``.
        """
        
        # Add `_user` to `defaults` because `kwargs` are used in the lookup,
        # but `defaults` eventually become keyword arguments passed to `create()`
        if defaults is None:
            defaults = {}
        
        defaults['_user'] = _user
        
        return super().get_or_create(defaults, **kwargs)
    
    def update(self, _user=None, **kwargs):
        """
        Overridden to ensure the ``user_modified`` and ``date_modified`` fields
        are always updated. The ``_user`` argument (named to reduce potential
        conflicts with model field names) is the user instance to update
        ``user_modified`` with. It is required unless the
        :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` setting is ``False``.
        """
        
        # TODO: Remove fallback setting in 1.0
        require_user = getattr(
            settings,
            'DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE',
            getattr(settings, 'DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE', True)  # backwards compat.
        )
        if require_user and not _user:
            raise TypeError('update() requires the first positional argument to be a user model instance.')
        
        kwargs.setdefault('date_modified', timezone.now())
        
        if _user:
            kwargs['user_modified'] = _user
        
        return super().update(**kwargs)
    
    def update_or_create(self, defaults=None, _user=None, **kwargs):
        """
        Overridden to ensure a user is provided to the ``save()`` call on the
        model instance, whether the record id being created or updated. The
        ``_user`` argument (named to reduce potential conflicts with model
        field names) is the user instance to pass through. It is required
        unless the :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE` setting
        is ``False``.
        """
        
        # TODO: Remove fallback setting in 1.0
        require_user = getattr(
            settings,
            'DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE',
            getattr(settings, 'DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE', True)  # backwards compat.
        )
        if require_user and not _user:
            raise TypeError('create() requires the first positional argument to be a user model instance.')
        
        # Add `_user` to `kwargs` rather than `defaults` as `_user` is its own
        # keyword argument to get_or_create() (which is called by super())
        kwargs['_user'] = _user
        
        #
        # The below is copied from QuerySet.update_or_create() (as at Django
        # 3.2.6) and changed to pass the `user` argument to save()
        #
        
        defaults = defaults or {}
        self._for_write = True
        with transaction.atomic(using=self.db):
            # Lock the row so that a concurrent update is blocked until
            # update_or_create() has performed its save.
            obj, created = self.select_for_update().get_or_create(defaults, **kwargs)
            if created:
                return obj, created
            
            for k, v in resolve_callables(defaults):
                setattr(obj, k, v)
                
            obj.save(_user, using=self.db)
        
        return obj, False
    
    def owned_by(self, user):
        """
        Return a queryset of records "owned" by the given user, as per the
        ``user_created`` field. ``user`` can be a ``User`` instance or an id.
        """
        
        return self.filter(user_created=user)


# Backwards compat.
# TODO: Remove in 1.0
class CommonInfoQuerySet(AuditableQuerySet):
    
    def __init__(self, *args, **kwargs):
        
        warnings.warn('Use of CommonInfoQuerySet is deprecated, use AuditableQuerySet instead.', DeprecationWarning)
        
        super().__init__(*args, **kwargs)


class Auditable(models.Model):
    """
    Model mixin that provides standard user and datetime fields (``user_created``,
    ``user_modified``, ``date_created`` and ``date_modified``) and overridden
    instance and queryset methods to enforce keeping those details up to date.
    
    WARNING: Models incorporating this mixin cannot be involved in any process
    process that automatically calls ``save()`` on the instance, or many
    queryset methods that create/update record (``create()``, ``update()``,
    etc), as it won't pass the required user argument. Any such processes will
    require modification to support the custom method signatures, or the
    enforcement of a known user will need to be disabled.
    """
    
    date_created = models.DateTimeField(editable=False, verbose_name='Date Created')
    date_modified = models.DateTimeField(editable=False, verbose_name='Date Last Modified')
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        verbose_name='User Created',
        related_name='+',
        on_delete=models.PROTECT
    )
    user_modified = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        verbose_name='User Last Modified',
        related_name='+',
        on_delete=models.PROTECT
    )
    
    objects = AuditableQuerySet.as_manager()
    
    class Meta:
        abstract = True
    
    def save(self, user=None, *args, **kwargs):
        """
        Overridden to ensure the ``user_modified`` and ``date_modified`` fields
        are always updated. The ``user`` argument is required and must be passed
        a ``User`` instance, unless the :setting:`DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE`
        setting is ``False``.
        """
        
        # TODO: Remove fallback setting in 1.0
        require_user = getattr(
            settings,
            'DJEM_AUDITABLE_REQUIRE_USER_ON_SAVE',
            getattr(settings, 'DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE', True)  # backwards compat.
        )
        if require_user and not user:
            raise TypeError("save() requires the 'user' argument")
        
        now = timezone.now()
        update_fields = []
        
        self.date_modified = now
        update_fields.append('date_modified')
        
        if user:
            self.user_modified = user
            update_fields.append('user_modified')
        
        if self.pk is None:
            if self.date_created is None:
                self.date_created = now
            
            if user:
                try:
                    self.user_created
                except ObjectDoesNotExist:
                    self.user_created = user
        
        if 'update_fields' in kwargs:
            # If only saving a subset of fields, make sure the fields altered
            # above are included. Not applicable when creating a new record,
            # so *_created fields can be ignored.
            kwargs['update_fields'] = set(kwargs['update_fields']).union(update_fields)
        
        super().save(*args, **kwargs)
    
    def owned_by(self, user):
        """
        Return ``True`` if ``user_created`` matches the given user, otherwise
        return ``False``. The user can be given as an id or a ``User`` instance.
        """
        
        try:
            user_id = user.pk
        except AttributeError:
            # Assume an id was given
            user_id = user
        
        return user_id == self.user_created_id


# Backwards compat.
# TODO: Remove in 1.0
class CommonInfoMixin(Auditable):
    
    def __init__(self, *args, **kwargs):
        
        warnings.warn('Use of CommonInfoMixin is deprecated, use Auditable instead.', DeprecationWarning)
        
        super().__init__(*args, **kwargs)
    
    class Meta:
        abstract = True


class ArchivableQuerySet(MixableQuerySet, models.QuerySet):
    """
    Provides custom functionality pertaining to the ``is_archived`` field
    provided by :class:`Archivable`.
    """
    
    def archived(self):
        """
        Filter the queryset to archived records (``is_archived=True``).
        """
        
        return self.filter(is_archived=True)
    
    def unarchived(self):
        """
        Filter the queryset to unarchived records (``is_archived=False``).
        """
        
        return self.filter(is_archived=False)


class Archivable(models.Model):
    """
    Model mixin that provides an ``is_archived`` Boolean field, multiple
    Managers to access querysets filtered on that flag and additional instance
    and queryset methods to set the flag.
    """
    
    is_archived = models.BooleanField(default=False, db_index=True)
    
    objects = ArchivableQuerySet.as_manager()
    
    class Meta:
        abstract = True
    
    def archive(self, *args, **kwargs):
        """
        Archive this record.
        
        Accepts all arguments of the ``save`` method, as it saves the instance
        after setting the ``is_archived`` flag. It saves using the
        ``update_fields`` keyword argument, containing the ``is_archived``
        field, whether it was provided to this method or not. If provided, it
        is extended, not replaced.
        """
        
        if 'update_fields' in kwargs:
            kwargs['update_fields'] = set(kwargs['update_fields']).union(('is_archived',))
        else:
            kwargs['update_fields'] = ('is_archived',)
        
        self.is_archived = True
        self.save(*args, **kwargs)
    
    def unarchive(self, *args, **kwargs):
        """
        Unarchive this record.
        
        Accepts all arguments of the ``save`` method, as it saves the instance
        after setting the ``is_archived`` flag. It saves using the
        ``update_fields`` keyword argument, containing the ``is_archived``
        field, whether it was provided to this method or not. If provided, it
        is extended, not replaced.
        """
        
        if 'update_fields' in kwargs:
            kwargs['update_fields'] = set(kwargs['update_fields']).union(('is_archived',))
        else:
            kwargs['update_fields'] = ('is_archived',)
        
        self.is_archived = False
        self.save(*args, **kwargs)


# Backwards compat.
# TODO: Remove in 1.0
class ArchivableMixin(Archivable):
    
    def __init__(self, *args, **kwargs):
        
        warnings.warn('Use of ArchivableMixin is deprecated, use Archivable instead.', DeprecationWarning)
        
        super().__init__(*args, **kwargs)
    
    class Meta:
        abstract = True


class VersionableQuerySet(MixableQuerySet, models.QuerySet):
    """
    Provides custom functionality pertaining to the ``version`` field
    provided by :class:`Versionable`.
    """
    
    def update(self, **kwargs):
        """
        Overridden to ensure the ``version`` field is always updated.
        """
        
        kwargs['version'] = models.F('version') + 1
        
        return super().update(**kwargs)


# Backwards compat.
# TODO: Remove in 1.0
class VersioningQuerySet(VersionableQuerySet):
    
    def __init__(self, *args, **kwargs):
        
        warnings.warn('Use of VersioningQuerySet is deprecated, use VersionableQuerySet instead.', DeprecationWarning)
        
        super().__init__(*args, **kwargs)


class Versionable(models.Model):
    """
    Model mixin that provides a ``version`` field that is automatically
    incremented on every save and overridden instance and manager methods to
    enforce keeping it up to date.
    
    WARNING: The version is atomically incremented using an F() expression. After
    a save, the field will no longer be accessible as an integer, and will raise
    AmbiguousVersionError if accessed. The instance will need to be requeried to
    get the new version. It can, however, be saved multiple times and the version
    will be correctly incremented each time.
    """
    
    # Model-specific version of the generic ModelAmbiguousVersionError exception
    class AmbiguousVersionError(ModelAmbiguousVersionError):
        pass
    
    version = models.PositiveIntegerField(editable=False, default=1)
    
    objects = VersionableQuerySet.as_manager()
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Overridden to ensure the ``version`` field is always updated.
        """
        
        incremented = False
        
        if self.pk:
            # Increment the version of this record. Does not happen on initial
            # save (when self.pk is None) as it is set to 1 by default.
            self.version = models.F('version') + 1
            incremented = True
            
            if 'update_fields' in kwargs:
                # If only saving a subset of fields, make sure the version
                # field is included.
                update_fields = set(kwargs['update_fields'])
                update_fields.add('version')
                kwargs['update_fields'] = update_fields
        
        super().save(*args, **kwargs)
        
        if incremented:
            # If the version has been incremented, make it inaccessible. It
            # cannot be accurately determined without re-querying for it, and
            # even getting an accurate version number does not mean it is the
            # version that correlates with the values of all other fields on
            # this instance. The only way to get all correlated values is to
            # re-query for the entire object. This is too much overhead to
            # impose on every save, especially when accessing the version after
            # a save will be an edge case. It will be up to application logic to
            # detect and handle the circumstance of an ambiguous version.
            self.version = SimpleLazyObject(self.AmbiguousVersionError._raise)


# Backwards compat.
# TODO: Remove in 1.0
class VersioningMixin(Versionable):
    
    def __init__(self, *args, **kwargs):
        
        warnings.warn('Use of VersioningMixin is deprecated, use Versionable instead.', DeprecationWarning)
        
        super().__init__(*args, **kwargs)
    
    class Meta:
        abstract = True


class StaticAbstractQuerySet(AuditableQuerySet, ArchivableQuerySet, VersionableQuerySet):
    """
    Combination of AuditableQuerySet, ArchivableQuerySet and VersionableQuerySet
    for use by managers of models that want the functionality of all three.
    """
    
    pass


class StaticAbstract(Auditable, Archivable, Versionable, models.Model):
    """
    Useful abstract base model combining the functionality of the Auditable,
    Archivable, and Versionable mixins.
    """
    
    objects = StaticAbstractQuerySet.as_manager()
    
    class Meta:
        abstract = True
