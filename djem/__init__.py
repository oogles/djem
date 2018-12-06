__version__ = '0.6.4'

# Shortcuts to quick-use utils
from djem.utils.mon import M, Mon, mon  # NOQA
from djem.utils.inspect import pp  # NOQA


class Undefined:
    
    def __bool__(self):
        
        return False
    
    # Python 2 compat.
    __nonzero__ = __bool__
    
    def __str__(self):
        
        return '<undefined>'


UNDEFINED = Undefined()
