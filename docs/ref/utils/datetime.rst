===============
Date/Time Utils
===============

.. module:: djem.utils.dt

``TimeZoneHelper``
==================

.. class:: TimeZoneHelper(tz)

    .. versionadded:: 0.3

    A simple helper class that provides shortcuts for getting the current date and the current datetime for a known local timezone.

    ``tz`` should be a valid timezone name string (as accepted by the ``pytz.timezone`` function) or a ``pytz`` ``tzinfo`` instance (as returned by the ``pytz.timezone`` function).

    .. attribute:: tz

        The ``pytz`` ``tzinfo`` instance representing the timezone used by this ``TimeZoneHelper`` instance.

    .. attribute:: name

        The name of the timezone represented by this ``TimeZoneHelper`` instance, as a string.
        Equivalent to ``tz.zone``, where ``tz`` is the :attr:`instance's tz attribute <TimeZoneHelper.tz>`.

    .. automethod:: now

    .. automethod:: today

    .. warning::

        Be careful when dealing with local times. Django recommends you "use UTC in the code and use local time only when interacting with end users", with the conversion from UTC to local time usually only being performed in templates. And the pytz documentation notes "The preferred way of dealing with times is to always work in UTC, converting to localtime only when generating output to be read by humans". See the `Django timezone documentation <https://docs.djangoproject.com/en/stable/topics/i18n/timezones/>`_ and the `pytz documentation <http://pytz.sourceforge.net/>`_.
