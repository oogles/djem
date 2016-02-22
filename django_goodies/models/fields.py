from django.core.exceptions import ValidationError
from django.db import models

from django_goodies.utils.dt import TimeZoneHelper

# Allow the file to be imported without pytz installed, though it is required
# to use TimeZoneField
try:
    import pytz
except ImportError:
    pytz = None


def _get_helper(tz):
    
    if tz in (None, ''):
        return None
    
    if isinstance(tz, TimeZoneHelper):
        return tz
    
    try:
        return TimeZoneHelper(tz)
    except pytz.UnknownTimeZoneError:
        raise ValidationError('Invalid timezone "{0}".'.format(tz))


class TimeZoneField(models.Field):
    """
    Stores a timezone and provides a helper object to access date/time-related
    functionality for that timezone.
    
    Valid inputs:
     - A timezone string (accepted by pytz.timezone())
     - An instance of pytz.tzinfo.BaseTzInfo
     - The pytz.UTC singleton
     - An instance of django_goodies.utils.dt.TimeZoneHelper
     - None and the empty string (both representing a null value)
    
    When the value of the field is not null, accessing the value of the field
    will output an instance of django_goodies.utils.dt.TimeZoneHelper,
    instantiated with the stored timezone.
    """
    
    description = "A pytz timezone"
    
    if pytz:
        CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    else:
        CHOICES = []
    
    MAX_LENGTH = 63
    
    def __init__(self, **kwargs):
        
        if not pytz:
            raise RuntimeError('TimeZoneField requires pytz to be installed.')
        
        kwargs.setdefault('choices', self.CHOICES)
        kwargs.setdefault('max_length', self.MAX_LENGTH)
        
        super(TimeZoneField, self).__init__(**kwargs)
    
    def get_internal_type(self):
        
        return 'CharField'
    
    def deconstruct(self):
        
        name, path, args, kwargs = super(TimeZoneField, self).deconstruct()
        
        # Only include choices and max_length kwargs if not the default
        if kwargs['choices'] == self.CHOICES:
            del kwargs['choices']
        
        if kwargs['max_length'] == self.MAX_LENGTH:
            del kwargs['max_length']
        
        return name, path, args, kwargs
    
    def get_default(self):
        
        # Convert string default to TimeZoneHelper
        value = super(TimeZoneField, self).get_default()
        return _get_helper(value)
    
    def from_db_value(self, value, expression, connection, context):
        
        # Convert to TimeZoneHelper
        return _get_helper(value)
    
    def to_python(self, value):
        
        # Convert to TimeZoneHelper
        return _get_helper(value)
    
    def get_prep_value(self, value):
        
        # Convert to timezone string, ensuring it is a valid timezone
        helper = _get_helper(value)
        
        if helper is None:
            return ''
        
        return helper.tz.zone
