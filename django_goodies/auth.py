from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied


class ObjectPermissionsBackend(object):
    
    def authenticate(self, *args, **kwargs):
        
        return None
    
    def _get_object_permission(self, perm, user_obj, obj, from_name):
        """
        Test if a user has a permission on a specific model object.
        ``from_name`` can be either "user" or "group", to determine permissions
        using the user object itself or the groups it belongs to, respectively.
        """
        
        if not user_obj.is_active:
            return False
        
        perm_cache_name = '_{0}_perm_cache_{1}_{2}'.format(from_name, perm, obj.pk)
        
        if not hasattr(user_obj, perm_cache_name):
            access_fn = getattr(obj, '_{0}_can_{1}'.format(
                from_name,
                perm.split('.')[-1]
            ), None)
            
            if not access_fn:
                # No function defined on obj to determine access - assume no
                # access
                access = False
            elif not user_obj.has_perm(perm):
                # The User needs to have model-level permissions in order to
                # get object-level permissions
                access = False
            else:
                try:
                    if from_name == 'user':
                        access = access_fn(user_obj)
                    else:
                        access = access_fn(user_obj.groups.all())
                except PermissionDenied:
                    access = False
            
            setattr(user_obj, perm_cache_name, access)
        
        return getattr(user_obj, perm_cache_name)
    
    def _get_object_permissions(self, user_obj, obj, from_name=None):
        """
        Return a set of the permissions a user has on a specific model object.
        ``from_name`` can be either "user" or "group", to determine permissions
        using the user object itself or the groups it belongs to, respectively.
        It can also be None to determine the users permissions from both sources.
        """
        
        if not user_obj.is_active or user_obj.is_anonymous() or not obj:
            return set()
        
        perms_for_model = Permission.objects.filter(
            content_type__app_label=obj._meta.app_label,
            content_type__model=obj._meta.model_name,
        ).values_list('content_type__app_label', 'codename')
        
        perms_for_model = ['{0}.{1}'.format(app, name) for app, name in perms_for_model]
        
        if user_obj.is_superuser:
            # Superusers get all permissions, regardless of obj or from_name
            perms = set(perms_for_model)
        else:
            perms = set()
            for perm in perms_for_model:
                access = False
                
                # Check user first, unless only checking for group
                if from_name != 'group':
                    access = self._get_object_permission(perm, user_obj, obj, 'user')
                
                # Check group if user didn't grant the permission, unless only
                # checking for user
                if not access and from_name != 'user':
                    access = self._get_object_permission(perm, user_obj, obj, 'group')
                
                if access:
                    perms.add(perm)
        
        return perms
    
    def get_user_permissions(self, user_obj, obj=None):
        
        return self._get_object_permissions(user_obj, obj, 'user')
    
    def get_group_permissions(self, user_obj, obj=None):
        
        return self._get_object_permissions(user_obj, obj, 'group')
    
    def get_all_permissions(self, user_obj, obj=None):
        
        return self._get_object_permissions(user_obj, obj)
    
    def has_perm(self, user_obj, perm, obj=None):
        
        if not obj:
            return False  # not dealing with non-object permissions
        
        return (
            self._get_object_permission(perm, user_obj, obj, 'user') or
            self._get_object_permission(perm, user_obj, obj, 'group')
        )
