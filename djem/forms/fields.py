from django import forms

from djem.utils.dt import TIMEZONE_CHOICES, get_tz_helper


# Based on django-timezone-field
# https://github.com/mfogel/django-timezone-field
# Not used by models.TimeZoneField, but provided for manually defined fields
# in Forms
class TimeZoneField(forms.TypedChoiceField):
    
    def __init__(self, *args, **kwargs):
        
        defaults = {
            'coerce': get_tz_helper,
            'choices': TIMEZONE_CHOICES
        }
        
        defaults.update(kwargs)
        
        super().__init__(*args, **defaults)
