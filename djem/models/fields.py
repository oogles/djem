from django.db import models

from djem.utils.dt import PYTZ_AVAILABLE, TIMEZONE_CHOICES, get_tz_helper

__all__ = ('TimeZoneField', )


# Based on django-timezone-field
# https://github.com/mfogel/django-timezone-field
class TimeZoneField(models.Field):
    """
    Stores a timezone and provides a helper object to access date/time-related
    functionality for that timezone.
    
    Valid inputs:
     - A timezone string (accepted by pytz.timezone())
     - An instance of pytz.tzinfo.BaseTzInfo
     - The pytz.UTC singleton
     - An instance of djem.utils.dt.TimeZoneHelper
     - None and the empty string (both representing a null value)
    
    When the value of the field is not null, accessing the value of the field
    will output an instance of djem.utils.dt.TimeZoneHelper,
    instantiated with the stored timezone.
    """
    
    description = "A pytz timezone"
    
    CHOICES = TIMEZONE_CHOICES
    MAX_LENGTH = 63
    
    def __init__(self, verbose_name=None, **kwargs):
        
        if not PYTZ_AVAILABLE:  # pragma: no cover
            raise RuntimeError('TimeZoneField requires pytz to be installed.')
        
        kwargs.setdefault('choices', self.CHOICES)
        kwargs.setdefault('max_length', self.MAX_LENGTH)
        
        super().__init__(verbose_name=verbose_name, **kwargs)
    
    def get_internal_type(self):
        
        return 'CharField'
    
    def deconstruct(self):
        
        name, path, args, kwargs = super().deconstruct()
        
        # Only include choices and max_length kwargs if not the default
        if kwargs['choices'] == self.CHOICES:
            del kwargs['choices']
        
        if kwargs['max_length'] == self.MAX_LENGTH:
            del kwargs['max_length']
        
        return name, path, args, kwargs
    
    def get_default(self):
        
        # Convert string default to TimeZoneHelper
        value = super().get_default()
        return get_tz_helper(value)
    
    def from_db_value(self, value, expression, connection):
        
        # Convert to TimeZoneHelper
        return get_tz_helper(value)
    
    def to_python(self, value):
        
        # Convert to TimeZoneHelper
        return get_tz_helper(value)
    
    def get_prep_value(self, value):
        
        # Convert to timezone string, ensuring it is a valid timezone
        helper = get_tz_helper(value)
        
        if helper is None:
            if self.null:
                return None
            else:
                return ''
        
        return helper.tz.zone
    
    def validate(self, value, model_instance):
        
        # Ensure the value is a valid TimeZoneHelper for a valid timezone
        value = get_tz_helper(value)
        
        # Only pass the helper's timezone name into the super call - it will
        # be checked for its presence in self.choices
        super().validate(value.tz.zone, model_instance)
