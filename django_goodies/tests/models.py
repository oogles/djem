from django.db import models

from ..models import CommonInfoMixin, ArchivableMixin, VersioningMixin, StaticAbstract

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
