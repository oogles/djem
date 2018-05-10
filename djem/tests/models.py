from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import PermissionDenied
from django.db import models

from djem.auth import OLPMixin
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
    
    def _user_can_change_commoninfotest(self, user):
        
        return user.pk == self.user_created_id


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
    field2 = models.BooleanField(default=True)


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


# Custom user model for testing OLPMixin
class CustomUser(OLPMixin, AbstractUser):
    
    # Override groups and user_permissions to avoid related_name clashes with
    # the same fields on the regular auth.User model
    groups = models.ManyToManyField(Group, related_name='+')
    user_permissions = models.ManyToManyField(Permission, related_name='+')


# Model for testing OLPMixin permission logging
class LogTest(models.Model):
    
    def __str__(self):
        
        return 'Log Test #{}'.format(self.pk)
    
    def _user_can_olp_logtest(self, user):
        
        user.log('This permission is restricted.')
        
        return False
    
    class Meta:
        permissions = (
            ('mlp_logtest', 'Permission with no object-level checks'),
            ('olp_logtest', 'Permission with object-level checks and additional logging'),
        )


# Model for testing object-level permissions with standard user model
class OLPTest(models.Model):
    
    user = models.ForeignKey('auth.User', null=True, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, on_delete=models.PROTECT)
    
    def _user_can_open_olptest(self, user):
        
        # For tests using inactive and super users (neither should reach this point)
        assert user.is_active or not user.is_superuser, 'Not supposed to get here'
        
        return True
    
    def _group_can_open_olptest(self, groups):
        
        return True
    
    def _user_can_user_only_olptest(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_user_only_olptest(self, groups):
        
        return False
    
    def _user_can_group_only_olptest(self, groups):
        
        return False
    
    def _group_can_group_only_olptest(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    def _user_can_combined_olptest(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_combined_olptest(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    def _user_can_deny_olptest(self, user):
        
        raise PermissionDenied()
    
    class Meta:
        permissions = (
            ('open_olptest', 'Completely open to anyone'),
            ('closed_olptest', 'Completely closed to everyone (except super users)'),
            ('user_only_olptest', 'Open to the user specified on the object'),
            ('group_only_olptest', 'Open to the group specified on the object'),
            ('combined_olptest', 'Open to any user OR group specified on the object'),
            ('deny_olptest', 'Denies permission by raising PermissionDenied for the user'),
        )


# Model for testing object-level permissions with custom user model incorporating OLPMixin
class UniversalOLPTest(models.Model):
    
    user = models.ForeignKey(CustomUser, null=True, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, on_delete=models.PROTECT)
    
    def _user_can_open_universalolptest(self, user):
        
        # For tests using inactive and super users (neither should reach this point)
        assert user.is_active or not user.is_superuser, 'Not supposed to get here'
        
        return True
    
    def _group_can_open_universalolptest(self, groups):
        
        return True
    
    def _user_can_user_only_universalolptest(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_user_only_universalolptest(self, groups):
        
        return False
    
    def _user_can_group_only_universalolptest(self, groups):
        
        return False
    
    def _group_can_group_only_universalolptest(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    def _user_can_combined_universalolptest(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_combined_universalolptest(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    def _user_can_deny_universalolptest(self, user):
        
        raise PermissionDenied()
    
    class Meta:
        permissions = (
            ('open_universalolptest', 'Completely open to anyone'),
            ('closed_universalolptest', 'Completely closed to everyone (except super users)'),
            ('user_only_universalolptest', 'Open to the user specified on the object'),
            ('group_only_universalolptest', 'Open to the group specified on the object'),
            ('combined_universalolptest', 'Open to any user OR group specified on the object'),
            ('deny_universalolptest', 'Denies permission by raising PermissionDenied for the user'),
        )
