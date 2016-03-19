Django Goodies Documentation
============================

Django Goodies is a collection of useful stuff for Django projects.


Installation
------------

Install the latest stable version from PyPI:

.. code-block:: bash
    
    pip install django-goodies


Goodies
-------

.. toctree::
    :maxdepth: 2
    
    ref/models
    ref/managers
    ref/model_fields
    ref/forms
    ref/form_fields
    ref/dateutils
    ref/exceptions


Dependencies
------------

.. currentmodule:: django_goodies

* `pytz <http://pytz.sourceforge.net/>`_ is required to make use of :class:`models.TimeZoneField`, :class:`forms.TimeZoneField` and :class:`~utils.dt.TimeZoneHelper`.


License
-------

The project is licensed under the BSD license.
