===========
Form Fields
===========

.. module:: djem.forms.fields

.. currentmodule:: djem.forms

``TimeZoneField``
=================

.. class:: TimeZoneField(**kwargs)

    A ``TypedChoiceField`` with defaults applied for ``coerce`` and ``choices``.

    * Default widget: ``Select``.
    * Empty value: ``''`` (the empty string), by default.
    * Normalizes to: a :class:`~djem.utils.dt.TimeZoneHelper` instance.
    * Validates that the given value exists in the list of choices and can be
      coerced.
    * Error message keys: ``required``, ``invalid_choice``.

    .. attribute:: TimeZoneField.coerce

        Defaults to a function that accepts a timezone name string ('Australia/Sydney', 'US/Eastern', etc) and returns a :class:`~djem.utils.dt.TimeZoneHelper` instance for that timezone.

    .. attribute:: TimeZoneField.choices

        Defaults to a list of 2-tuples containing the timezones provided by `pytz.common_timezones <http://pytz.sourceforge.net/#helpers>`_. Both items of each 2-tuple simply contain the timezone name. This is equavalient to:

        .. code-block:: python

            choices = [(tz, tz) for tz in pytz.common_timezones]

    .. note::

        Use of ``TimeZoneField`` requires `pytz <http://pytz.sourceforge.net/>`_ to be installed. If ``pytz`` is not available, the default ``choices`` list will be empty and no :class:`~djem.utils.dt.TimeZoneHelper` objects will be able to be instantiated.

    .. note::

        Use of ``TimeZoneField`` only makes sense if `USE_TZ <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-USE_TZ>`_ is True.

    .. seealso::

        The :class:`djem.models.TimeZoneField` model field.
