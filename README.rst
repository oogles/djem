Django Goodies
==============

A collection of useful stuff for Django projects, including:

 - **verify**: a view function decorator that will verify a view argument as a valid id against a given model. When the id is valid, the argument value will be replaced by the valid model instance. When the id is not valid, the decorator will issue a redirect to the configured fallback view.

Includes full test suite.
Only tested on Django 1.7.0.


Installation
------------

Install the latest stable version from PyPI:

.. code-block:: bash
    
    pip install django-goodies


Documentation
-------------

Full documentation can be found at: http://django-goodies.readthedocs.org.


Thanks
------

The project-independent test platform was inspired by https://github.com/dabapps/django-reusable-app
