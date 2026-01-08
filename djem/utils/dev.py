from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission


class Developer:
    """
    Designed for use within the Django shell to aid developers in performing
    regular operations used for testing and debugging, primarily regarding
    altering aspects of the developer's own user record.
    """
    
    awesome = {
        'is_staff': True,
        'is_superuser': True
    }
    
    boring = {
        'is_staff': False,
        'is_superuser': False
    }
    
    def __init__(self, **user_lookup_kwargs):
        
        self.user_lookup_kwargs = user_lookup_kwargs
    
    @property
    def user(self):
        """
        The developer's associated user model instance, as given by
        ``django.contrib.auth.get_user_model()``, and looked up using the
        keyword arguments given to the constructor or defined by the
        :setting:`DJEM_DEV_USER` setting.
        """
        
        if not hasattr(self, '_user'):
            if not self.user_lookup_kwargs:
                self.user_lookup_kwargs = getattr(settings, 'DJEM_DEV_USER', {})
            
            self._user = get_user_model().objects.get(**self.user_lookup_kwargs)
        
        return self._user
    
    def be_awesome(self):
        """
        Assign :attr:`user` the attributes defined in :attr:`awesome`.
        """
        
        user = self.user
        
        for attr, value in self.awesome.items():
            setattr(user, attr, value)
        
        user.save(update_fields=self.awesome.keys())
    
    def be_boring(self):
        """
        Assign :attr:`user` the attributes defined in :attr:`boring`.
        """
        
        user = self.user
        
        for attr, value in self.boring.items():
            setattr(user, attr, value)
        
        user.save(update_fields=self.boring.keys())
    
    def no_super(self):
        """
        Set the ``is_superuser=False`` flag on :attr:`user`.
        """
        
        user = self.user
        user.is_superuser = False
        user.save(update_fields=('is_superuser', ))
    
    def no_staff(self):
        """
        Set the ``is_staff=False`` flag on :attr:`user`.
        """
        
        user = self.user
        user.is_staff = False
        user.save(update_fields=('is_staff', ))
    
    def add_permissions(self, *permissions):
        """
        Assign :attr:`user` the given permissions (by codename).
        """
        
        permissions = Permission.objects.filter(codename__in=permissions)
        
        for perm in permissions:
            self.user.user_permissions.add(perm)
    
    def remove_permissions(self, *permissions):
        """
        Remove the given permissions (by codename) from :attr:`user`.
        """
        
        permissions = Permission.objects.filter(codename__in=permissions)
        
        for perm in permissions:
            self.user.user_permissions.remove(perm)
