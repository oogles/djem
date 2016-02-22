# Date, time and timezone utils

from django.utils import six, timezone

# Allow the file to be imported without pytz installed, though it is required
# to use TimeZoneHelper
try:
    import pytz
except ImportError:
    pytz = None


class TimeZoneHelper(object):
    
    def __init__(self, tz):
        
        if not pytz:
            raise RuntimeError('TimeZoneHelper requires pytz to be installed.')
        
        if isinstance(tz, six.string_types):
            tz = pytz.timezone(tz)
        
        self.tz = tz
    
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
