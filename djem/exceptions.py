
class ModelAmbiguousVersionError(Exception):
    """
    Raised when a model's ``version`` field contains an ambiguous value, such
    as after it has been atomically incremented.
    """
    
    def __init__(self):
        
        super(ModelAmbiguousVersionError, self).__init__(
            'This instance\'s version has been atomically incremented and '
            'therefore its value, as associated with the current values of '
            'other fields on the instance, cannot be accurately determined.'
        )
    
    @classmethod
    def _raise(cls):
        
        raise cls()
