__version__ = '0.9.0a2'

# Shortcuts to quick-use utils
from djem.utils.inspect import pp  # NOQA
from djem.utils.mon import M, Mon, mon  # NOQA


class Undefined:
    
    def __bool__(self):
        
        return False
    
    def __str__(self):
        
        return '<undefined>'
    
    def __deepcopy__(self, memo):
        
        return self


UNDEFINED = Undefined()
