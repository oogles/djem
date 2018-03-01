from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.base import ModelBase
from django.utils import six, timezone
from django.utils.functional import SimpleLazyObject

from djem.exceptions import ModelAmbiguousVersionError
from djem.models.managers import (
    ArchivableManager, CommonInfoManager, StaticAbstractManager,
    VersioningManager
)


class CommonInfoMixinBase(ModelBase):
    """
    Metaclass for adding appropriately named permission checking methods to
    concrete subclasses of CommonInfoMixin.
    As a reasonable default, "change" and "delete" permissions for such a
    subclass can be mapped to the ``owned_by`` method, granting owners the
    permissions and denying others.
    The permissions themselves will contain the name of the subclass model, so
    must be added dynamically once the name is known.
    """
    
    def __init__(cls, *args, **kwargs):
        
        name = cls._meta.model_name
        
        if not cls._meta.abstract:
            change_attr_name = '_user_can_change_{0}'.format(name)
            if not hasattr(cls, change_attr_name):
                setattr(cls, change_attr_name, lambda self, user: self.owned_by(user))
            
            delete_attr_name = '_user_can_delete_{0}'.format(name)
            if not hasattr(cls, delete_attr_name):
                setattr(cls, delete_attr_name, lambda self, user: self.owned_by(user))
        
        super(CommonInfoMixinBase, cls).__init__(*args, **kwargs)


class CommonInfoMixin(six.with_metaclass(CommonInfoMixinBase, models.Model)):
    """
    Model mixin that provides standard user and datetime fields (``user_created``,
    ``user_modified``, ``date_created`` and ``date_modified``) and overridden
    instance and manager methods to enforce keeping those details up to date.
    
    WARNING: Models incorporating this mixin cannot be involved in any process
    process that automatically calls ``save`` on the instance, or ``update`` on
    on the manager/queryset, as it won't pass the required user argument.
    For example, the queryset methods ``create`` and ``get_or_create`` will fail,
    as will saves performed by ModelForms that aren't overridden to support the
    custom signature.
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
    
    objects = CommonInfoManager()
    
    class Meta:
        abstract = True
    
    def save(self, user=None, *args, **kwargs):
        """
        Overridden to ensure the ``user_modified`` and ``date_modified`` fields
        are always updated. The ``user`` argument is required and must be passed
        a ``User`` instance, unless the ``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE``
        setting is ``False``.
        """
        
        require_user = getattr(settings, 'DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE', True)
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
        
        super(CommonInfoMixin, self).save(*args, **kwargs)
    
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


class ArchivableMixin(models.Model):
    """
    Model mixin that provides an ``is_archived`` Boolean field, multiple
    Managers to access querysets filtered on that flag and additional instance
    and queryset methods to set the flag.
    """
    
    is_archived = models.BooleanField(default=False, db_index=True)
    
    objects = ArchivableManager()
    live = ArchivableManager(archived=False)
    archived = ArchivableManager(archived=True)
    
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


class VersioningMixin(models.Model):
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
    
    objects = VersioningManager()
    
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
        
        super(VersioningMixin, self).save(*args, **kwargs)
        
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


class StaticAbstract(CommonInfoMixin, ArchivableMixin, VersioningMixin, models.Model):
    """
    Useful abstract base model combining the functionality of CommonInfoMixin,
    ArchivableMixing and VersioningMixin.
    """
    
    objects = StaticAbstractManager()
    live = StaticAbstractManager(archived=False)
    archived = StaticAbstractManager(archived=True)
    
    class Meta:
        abstract = True
