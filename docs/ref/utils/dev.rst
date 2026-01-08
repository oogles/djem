=========
Dev Utils
=========

.. module:: djem.utils.dev

``Developer``
=============

.. autoclass:: Developer
    
    .. autoattribute:: awesome
    .. autoattribute:: boring
    
    .. autoattribute:: user
    
    .. automethod:: be_awesome
    .. automethod:: be_boring
    .. automethod:: no_super
    .. automethod:: no_staff
    .. automethod:: add_permissions
    .. automethod:: remove_permissions
    
    As an example, a project may define a generic ``Developer`` instance that adopts whichever user details are configured by :setting:`DJEM_DEV_USER` (and environment-specific settings can be used to make this specific to individual developers). It may also define some more specific instances for explicit users. It may even customise which attributes are considered "awesome" or "boring" for that project. All together, this might look like:
    
    .. code-block:: python
        
        from django.conf import settings
        from djem.utils.dev import Developer
        
        class CustomDeveloper(Developer):
            
            awesome = {
                'is_superuser': True,
                'is_developer': True
            }
            boring = {
                'is_superuser': False,
                'is_developer': False
            }
        
        Me = CustomDeveloper()  # use DJEM_DEV_USER
        System = CustomDeveloper(username='system.user')
    
    As of Django 5.2, the ``shell`` management command can be configured with `extra automatic imports <https://docs.djangoproject.com/en/6.0/howto/custom-shell/#customize-automatic-imports>`_. A project's ``Developer`` instances are an excellent candidate for this feature, so they are automatically available in shell sessions for easy access. This is an example custom ``shell`` management command that includes the above example ``Developer`` instances, assuming they are defined in ``myproject.utils.dev``:
    
    .. code-block:: python
        
        from django.core.management.commands import shell
        
        class Command(shell.Command):
            
            def get_auto_imports(self):
                
                imports = super().get_auto_imports()
                
                imports.extend((
                    'myproject.utils.dev.Me',
                    'myproject.utils.dev.System'
                ))
                
                return imports
