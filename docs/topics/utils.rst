=====
Utils
=====

.. currentmodule:: djem

``UNDEFINED``
=============

.. versionadded:: 0.7

The :const:`UNDEFINED` constant is designed for use in argument default values.

Sometimes it is necessary to know whether *any* value was passed into a function or not, including values traditionally used as argument defaults (such as ``None``, ``False``, etc). Any given value could have an explicit meaning, with some default behaviour only performed if *nothing* was passed in.

Take the following contrived example:

.. code-block:: python

    def make_thing(name, label=None):

        if not label:
            label = name

        ...

The ``make_thing`` function takes a required ``name`` argument and an optional ``label`` argument. The label defaults to the name unless overridden with something more meaningful/verbose. But what if the caller would like their thing to have *no label*? And what if ``None``, ``False`` or an empty string could all indicate that? The function needs to differentiate those values from *nothing* being provided.

This example could be rewritten using :const:`UNDEFINED` in place of ``None`` as the argument default, allowing the caller to explicitly pass ``None`` to indicate that the label should not be given a default value:

.. code-block:: python

    from djem import UNDEFINED

    def make_thing(name, label=UNDEFINED):

        if label is UNDEFINED:
            label = name

        ...

:const:`UNDEFINED` is "falsey", so can also be used in more generic conditional statements:

.. code-block:: python

    from djem import UNDEFINED

    value = UNDEFINED

    if value:
        print('truthy')
    else:
        print('falsey')

    # output: 'falsey'


.. module:: djem.utils.dev

``Developer``
=============

:class:`Developer` is a class designed for use within the Django shell to aid developers in performing regular operations used for testing and debugging, primarily regarding accessing the developer's user record and altering aspects of that record.

Individual projects can define their own :class:`Developer` subclasses to suit their needs, and create instances representing individual developers. The :setting:`DJEM_DEV_USER` setting can also be used to avoid hardcoding numerous :class:`Developer` instances. Using environment-specific settings, a single instance can be used by any developer.

The following is an example of a basic extension of :class:`Developer`, and the definition of a couple of useful instances:

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

As of Django 5.2, the ``shell`` management command can be configured with `extra automatic imports <https://docs.djangoproject.com/en/6.0/howto/custom-shell/#customize-automatic-imports>`_. A project's :class:`Developer` instances are an excellent candidate for this feature, so they are automatically available in shell sessions for easy access. This is an example custom ``shell`` management command that includes the above example :class:`Developer` instances, assuming they are defined in ``myproject.utils.dev``:

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
