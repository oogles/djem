# Date, time and timezone utils

from django.core.exceptions import ValidationError
from django.utils import timezone

# Allow the file to be imported without pytz installed, though it is required
# to use TimeZoneHelper and other timezone-related functionality
try:
    import pytz
except ImportError:  # pragma: no cover
    pytz = None
    PYTZ_AVAILABLE = False
    TIMEZONE_CHOICES = []
else:
    PYTZ_AVAILABLE = True
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]


class TimeZoneHelper:
    
    def __init__(self, tz):
        
        if not PYTZ_AVAILABLE:  # pragma: no cover
            raise RuntimeError('TimeZoneHelper requires pytz to be installed.')
        
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
        
        self.tz = tz
    
    @property
    def name(self):
        
        return self.tz.zone
    
    def now(self):
        """
        Return the current datetime in the local timezone.
        """
        
        utc_now = timezone.now()
        return self.tz.normalize(utc_now.astimezone(self.tz))
    
    def today(self):
        """
        Return the current date in the local timezone.
        """
        
        return self.now().date()
    
    def __str__(self):
        
        return self.name
    
    def __repr__(self):
        
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))


def get_tz_helper(value):
    """
    Return an instance of TimeZoneHelper based on the given value.
    Valid values are:
     - A timezone string (accepted by pytz.timezone())
     - An instance of pytz.tzinfo.BaseTzInfo
     - The pytz.UTC singleton
    
    Return None if the value is None or the empty string.
    Raise ValidationError if the value cannot be converted into a pytz timezone.
    """
    
    if value in (None, ''):
        return None
    
    if isinstance(value, TimeZoneHelper):
        return value
    
    try:
        return TimeZoneHelper(value)
    except pytz.UnknownTimeZoneError:
        raise ValidationError('Invalid timezone "{0}".'.format(value))
