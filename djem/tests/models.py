from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import models

from djem.models import (
    ArchivableMixin, CommonInfoMixin, StaticAbstract, TimeZoneField,
    VersioningMixin
)


class CommonInfoTest(CommonInfoMixin, models.Model):
    """
    This model provides a concrete model with the CommonInfoMixin for testing
    the mixin without introducing the variables of a real subclass.
    """
    
    field1 = models.BooleanField(default=True)
    field2 = models.BooleanField(default=True)


class ArchivableTest(ArchivableMixin, models.Model):
    """
    This model provides a concrete model with the ArchivableMixin for testing
    the mixin without introducing the variables of a real subclass.
    """
    
    field1 = models.BooleanField(default=True)
    field2 = models.BooleanField(default=True)


class VersioningTest(VersioningMixin, models.Model):
    """
    This model provides a concrete model with the VersioningMixin for testing
    the mixin without introducing the variables of a real subclass.
    """
    
    field1 = models.BooleanField(default=True)
    field2 = models.BooleanField(default=True)


class StaticTest(StaticAbstract):
    """
    This model provides a concrete version of the abstract StaticAbstract
    model for testing elements of StaticAbstract without introducing the
    variables of a real subclass.
    It also provides a test bed for object-level permissions, both using defaults
    inherited from CommonInfoMixin and model-specific overrides.
    """
    
    field1 = models.BooleanField(default=True)
    
    # Customise permission access functions for testing
    def _user_can_change_statictest(self, user):
        
        return self.owned_by(user) or self.field1
    
    def _user_can_delete_statictest(self, user):
        
        return self.owned_by(user) or self.field1
    
    def _group_can_delete_statictest(self, groups):
        
        return groups.exists() and self.field1


class TimeZoneTest(models.Model):
    """
    This model provides some TimeZoneFields for testing.
    """
    
    timezone = TimeZoneField()
    timezone2 = TimeZoneField(default='Australia/Sydney')
    timezone3 = TimeZoneField(null=True)
    timezone4 = TimeZoneField(max_length=32, choices=(
        ('Australia/Sydney', 'Australia/Sydney'),
        ('Australia/Melbourne', 'Australia/Melbourne'),
        ('invalid', 'Invalid'),
    ))


class OPTest(models.Model):
    """
    This model provides some access functions for object-level permissions testing.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, on_delete=models.PROTECT)
    
    def _user_can_open_perm(self, user):
        
        # For tests using inactive and super users (neither should reach this point)
        assert user.is_active or not user.is_superuser, 'Not supposed to get here'
        
        return True
    
    def _group_can_open_perm(self, groups):
        
        return True
    
    def _user_can_user_only_perm(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_user_only_perm(self, groups):
        
        return False
    
    def _user_can_group_only_perm(self, groups):
        
        return False
    
    def _group_can_group_only_perm(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    def _user_can_combined_perm(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_combined_perm(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    def _user_can_deny_perm(self, user):
        
        raise PermissionDenied()
    
    class Meta:
        permissions = (
            ('open_perm', 'Completely open to anyone'),
            ('closed_perm', 'Completely closed to everyone (except super users)'),
            ('user_only_perm', 'Open to the user specified on the object'),
            ('group_only_perm', 'Open to the group specified on the object'),
            ('combined_perm', 'Open to any user OR group specified on the object'),
            ('deny_perm', 'Denies permission by raising PermissionDenied for the user'),
        )
