class Undefined:
    
    def __bool__(self):
        
        return False
    
    def __str__(self):
        
        return '<undefined>'
    
    def __deepcopy__(self, memo):
        
        return self


UNDEFINED = Undefined()
