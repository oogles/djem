==================
Djem Documentation
==================

Djem is a collection of useful stuff for Django projects.


Requirements
============

.. currentmodule:: djem

* Django 2.2+
* `pytz <http://pytz.sourceforge.net/>`_ is required to make use of :class:`models.TimeZoneField`, :class:`forms.TimeZoneField` and :class:`~utils.dt.TimeZoneHelper`.


Installation
============

Install the latest stable version from PyPI:

.. code-block:: bash

    pip install djem


Features
========

.. toctree::
    :maxdepth: 2

    topics/permissions/index
    topics/logging
    topics/models
    topics/forms
    topics/pagination
    topics/ajax
    topics/testing
    topics/utils
    ref/index
    changelog


License
=======

Djem is released under the `BSD license <https://github.com/oogles/djem/blob/master/LICENSE>`_.
