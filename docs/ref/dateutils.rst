===============
Date/Time Utils
===============

.. module:: django_goodies.utils.dt

``TimeZoneHelper``
==================

.. class:: TimeZoneHelper(tz)
    
    .. versionadded:: 0.3
    
    A simple helper class that provides shortcuts for getting the current date and the current datetime for a known local timezone.
    
    ``tz`` should be a valid timezone name string, as accepted by the ``pytz.timezone`` function.
    
    .. automethod:: now
    
    .. automethod:: today
    
    .. warning::
        
        Be careful when dealing with local times. Django recommends you "use UTC in the code and use local time only when interacting with end users", with the conversion from UTC to local time usually only being performed in templates. And the pytz documentation notes "The preferred way of dealing with times is to always work in UTC, converting to localtime only when generating output to be read by humans". See the `Django timezone documentation <https://docs.djangoproject.com/en/1.9/topics/i18n/timezones/>`_ and the `pytz documentation <http://pytz.sourceforge.net/>`_.
