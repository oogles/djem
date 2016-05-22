from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models

from django_goodies.models import (
    ArchivableMixin, CommonInfoMixin, StaticAbstract, TimeZoneField,
    VersioningMixin
)


class CommonInfoTest(CommonInfoMixin, models.Model):
    """
    This model simply provides a concrete model with the CommonInfoMixin,
    purely for testing the mixin without introducing the variables of a real
    subclass.
    """
    
    test = models.BooleanField(default=True)


class ArchivableTest(ArchivableMixin, models.Model):
    """
    This model simply provides a concrete model with the ArchivableMixin,
    purely for testing the mixin without introducing the variables of a real
    subclass.
    """
    
    test = models.BooleanField(default=True)


class VersioningTest(VersioningMixin, models.Model):
    """
    This model simply provides a concrete model with the VersioningMixin,
    purely for testing the mixin without introducing the variables of a real
    subclass.
    """
    
    test = models.BooleanField(default=True)


class StaticTest(StaticAbstract):
    """
    This model simply provides a concrete version of the abstract StaticAbstract
    model, purely for testing elements of StaticAbstract without introducing the
    variables of a real subclass.
    """
    
    pass


class TimeZoneTest(models.Model):
    """
    This model simply provides some TimeZoneFields for testing.
    """
    
    timezone = TimeZoneField()
    timezone2 = TimeZoneField(default='Australia/Sydney')
    timezone3 = TimeZoneField(null=True)


class OPTest(models.Model):
    """
    This model simply provides some access functions for object-level
    permissions testing.
    """
    
    test = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    group = models.ForeignKey(Group, null=True)
    
    def _user_can_view_optest(self, user):
        
        return True
    
    def _group_can_view_optest(self, user):
        
        return True
    
    def _user_can_change_optest(self, user):
        
        if not user.is_active or user.is_superuser:
            # For tests using inactive and super users
            raise AssertionError('Not supposed to get here')
        
        return True
    
    def _user_can_delete_optest(self, user):
        
        return user.pk == self.user_id
    
    def _group_can_delete_optest(self, groups):
        
        return groups.filter(pk=self.group_id).exists()
    
    class Meta:
        permissions = (
            ('view_optest', 'Can view an OPTest record.'),
        )
    
