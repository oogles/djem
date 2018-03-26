import re

from django.conf import settings
from django.db import models
from django.utils import timezone

whitespace_regex = re.compile(r'\W+')


class CommonInfoQuerySet(models.QuerySet):
    """
    Provides custom functionality pertaining to the fields provided by
    ``CommonInfoMixin``.
    """
    
    def update(self, user=None, **kwargs):
        """
        Overridden to ensure the ``user_modified`` and ``date_modified`` fields
        are always updated. The ``user`` argument is required and must be passed
        a ``User`` instance, unless the ``DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE``
        setting is ``False``.
        """
        
        require_user = getattr(settings, 'DJEM_COMMON_INFO_REQUIRE_USER_ON_SAVE', True)
        if require_user and not user:
            raise TypeError("save() requires the 'user' argument")
        
        kwargs['date_modified'] = timezone.now()
        
        if user:
            kwargs['user_modified'] = user
        
        return super(CommonInfoQuerySet, self).update(**kwargs)
    
    def owned_by(self, user):
        """
        Return a queryset of records "owned" by the given user, as per the
        ``user_created`` field. ``user`` can be a ``User`` instance or an id.
        """
        
        return self.filter(user_created=user)


# Implementation of a plain Manager providing access to CommonInfoQuerySet
CommonInfoManager = models.Manager.from_queryset(CommonInfoQuerySet)


class ArchivableQuerySet(models.QuerySet):
    """
    Provides custom functionality pertaining to the ``is_archived`` field
    provided by ``ArchivableMixin``.
    """
    
    def archived(self):
        
        return self.filter(is_archived=True)
    
    def unarchived(self):
        
        return self.filter(is_archived=False)


# Implementation of a plain Manager providing access to ArchivableQuerySet
ArchivableManager = models.Manager.from_queryset(ArchivableQuerySet)


class VersioningQuerySet(models.QuerySet):
    """
    Provides custom functionality pertaining to the ``version`` field
    provided by ``VersioningMixin``.
    """
    
    def update(self, **kwargs):
        """
        Overridden to ensure the ``version`` field is always updated.
        """
        
        kwargs['version'] = models.F('version') + 1
        
        return super(VersioningQuerySet, self).update(**kwargs)


# Implementation of a plain Manager providing access to VersioningQuerySet
VersioningManager = models.Manager.from_queryset(VersioningQuerySet)


class StaticAbstractQuerySet(CommonInfoQuerySet, ArchivableQuerySet, VersioningQuerySet):
    """
    Combination of CommonInfoQuerySet, ArchivableQuerySet and VersioningQuerySet
    for use by managers of models that want the functionality of all three.
    """
    
    def archive(self, user):
        """
        Archive all records in the current queryset.
        """
        
        self.update(user, is_archived=True)
    
    def unarchive(self, user):
        """
        Unarchive all records in the current queryset.
        """
        
        self.update(user, is_archived=False)


class StaticAbstractManager(ArchivableManager, CommonInfoManager, VersioningManager):
    """
    Combination of CommonInfoManager, ArchivableManager and VersioningManager
    for use by models that want the functionality of all three.
    """
    
    def __init__(self, *args, **kwargs):
        
        self.archived = kwargs.pop('archived', None)
        
        super(StaticAbstractManager, self).__init__(*args, **kwargs)
    
    def get_queryset(self):
        
        qs = StaticAbstractQuerySet(self.model, using=self._db)
        
        if self.archived is not None:
            qs = qs.filter(is_archived=self.archived)
        
        return qs
