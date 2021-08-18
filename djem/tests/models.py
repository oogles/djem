from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import PermissionDenied
from django.db import models

from djem.models import (
    Archivable, Auditable, Loggable, OLPMixin, StaticAbstract, TimeZoneField,
    Versionable
)


class AuditableTest(Auditable, models.Model):
    """
    This model provides a concrete model with the Auditable mixin for testing.
    """
    
    field1 = models.BooleanField(default=True)
    field2 = models.BooleanField(default=True)
    
    def _user_can_change_auditabletest(self, user):
        
        return user.pk == self.user_created_id


class ArchivableTest(Archivable, models.Model):
    """
    This model provides a concrete model with the Archivable for testing.
    """
    
    field1 = models.BooleanField(default=True)
    field2 = models.BooleanField(default=True)


class VersionableTest(Versionable, models.Model):
    """
    This model provides a concrete model with the Versionable mixin for testing.
    """
    
    field1 = models.BooleanField(default=True)
    field2 = models.BooleanField(default=True)


class StaticTest(StaticAbstract):
    """
    This model provides a concrete version of the abstract StaticAbstract
    model for testing.
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


class LogTest(Loggable, models.Model):
    """
    This model provides a concrete model with the Loggable mixin for testing.
    """
    
    field = models.BooleanField(default=True)


class CustomUser(OLPMixin, AbstractUser):
    """
    This is a custom user model for testing OLPMixin.
    """
    
    # Override groups and user_permissions to avoid related_name clashes with
    # the same fields on the regular auth.User model
    groups = models.ManyToManyField(Group, related_name='+')
    user_permissions = models.ManyToManyField(Permission, related_name='+')


class UserLogTest(models.Model):
    """
    This is a contrived model for testing OLPMixin permission logging.
    """
    
    class Meta:
        permissions = (
            ('mlp_log', 'Permission with no object-level checks'),
            ('olp_log', 'Permission with object-level checks and additional logging'),
        )
        
        # For test consistency across versions - due to the lack of a default
        # "view" permission prior to Django 2.1
        default_permissions = ('view', 'add', 'change', 'delete')
    
    def __str__(self):
        
        return 'Log Test #{}'.format(self.pk)
    
    def _user_can_olp_log(self, user):
        
        user.log('This permission is restricted.')
        
        return False


class OLPTest(models.Model):
    """
    This is a contrived model for testing object-level permissions with the
    standard user model.
    """
    
    user = models.ForeignKey('auth.User', null=True, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, on_delete=models.PROTECT)
    
    class Meta:
        permissions = (
            ('open_olptest', 'Completely open to anyone'),
            ('closed_olptest', 'Completely closed to everyone (except super users)'),
            ('user_only_olptest', 'Open to the user specified on the object'),
            ('group_only_olptest', 'Open to the group specified on the object'),
            ('combined_olptest', 'Open to any user OR group specified on the object'),
            ('deny_olptest', 'Denies permission by raising PermissionDenied for the user'),
        )
        
        # For test consistency across versions - due to the lack of a default
        # "view" permission prior to Django 2.1
        default_permissions = ('view', 'add', 'change', 'delete')
    
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

 
class UniversalOLPTest(models.Model):
    """
    This is a contrived model for testing object-level permissions with the
    above custom user model incorporating OLPMixin.
    """
    
    user = models.ForeignKey(CustomUser, null=True, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, on_delete=models.PROTECT)
    
    class Meta:
        permissions = (
            ('open_universalolptest', 'Completely open to anyone'),
            ('closed_universalolptest', 'Completely closed to everyone (except super users)'),
            ('user_only_universalolptest', 'Open to the user specified on the object'),
            ('group_only_universalolptest', 'Open to the group specified on the object'),
            ('combined_universalolptest', 'Open to any user OR group specified on the object'),
            ('deny_universalolptest', 'Denies permission by raising PermissionDenied for the user'),
        )
        
        # For test consistency across versions - due to the lack of a default
        # "view" permission prior to Django 2.1
        default_permissions = ('view', 'add', 'change', 'delete')
    
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
