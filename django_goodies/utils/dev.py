from django.contrib.auth import get_user_model


class Developer(object):
    """
    Designed for use within the Django shell to aid developers in performing
    regular operations used for testing and debugging, primarily regarding
    altering aspects of the developer's own User.
    """
    
    def __init__(self, **user_lookup_kwargs):
        
        self.user_lookup_kwargs = user_lookup_kwargs
    
    @property
    def user(self):
        
        if not hasattr(self, '_user'):
            self._user = get_user_model().objects.get(**self.user_lookup_kwargs)
        
        return self._user
    
    def be_awesome(self):
        
        user = self.user
        user.is_staff = True
        user.is_superuser = True
        user.save()
    
    def be_lame(self):
        
        user = self.user
        user.is_staff = False
        user.is_superuser = False
        user.save()
    
    def no_super(self):
        
        user = self.user
        user.is_superuser = False
        user.save()
    
    def no_staff(self):
        
        user = self.user
        user.is_staff = False
        user.save()
