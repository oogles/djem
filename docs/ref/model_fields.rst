============
Model Fields
============

.. module:: django_goodies.models.fields

.. currentmodule:: django_goodies.models

``TimeZoneField``
=================

.. class:: TimeZoneField(**kwargs)
    
    .. versionadded:: 0.3
    
    ``TimeZoneField`` is a model field that stores timezone name strings ('Australia/Sydney', 'US/Eastern', etc) in the database and provides access to :class:`~django_goodies.utils.dt.TimeZoneHelper` instances for the stored timezones.
    
    The default form field is a ``TypedChoiceField`` with a ``Select`` widget.
    
    ``TimeZoneField`` provides default values for the following constructor arguments:
    
    .. attribute:: TimeZoneField.choices
        
        Defaults to a list of 2-tuples containing the timezones provided by `pytz.common_timezones <http://pytz.sourceforge.net/#helpers>`_. Both items of each 2-tuple simply contain the timezone name. This is equavalient to:
        
        .. code-block:: python
            
            choices = [(tz, tz) for tz in pytz.common_timezones]
        
        If passing in a custom list of choices, it must match this format.
        The default value is stored on ``TimeZoneField`` in the ``CHOICES`` constant.
    
    .. attribute:: TimeZoneField.max_length
        
        Defaults to 63. This default value is stored on ``TimeZoneField`` in the ``MAX_LENGTH`` constant.
    
    Example, using ``TimeZoneField`` on a custom User model:
    
    .. code-block:: python
        
        # models.py
        from django.contrib.auth.models import AbstractBaseUser
        from django_goodies.models import TimeZoneField
        
        class CustomUser(AbstractBaseUser):
            ...
            time_zone = models.TimeZoneField()
    
    .. code-block:: python
        
        >>> user = CustomUser.objects.filter(timezone='Australia/Sydney').first()
        >>> user.timezone
        <TimeZoneHelper: Australia/Sydney>
    
    .. note::
        
        Use of ``TimeZoneField`` requires `pytz <http://pytz.sourceforge.net/>`_ to be installed. It will raise an exception during instantiation if ``pytz`` is not available.
    
    .. note::
        
        Use of ``TimeZoneField`` only makes sense if `USE_TZ <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-USE_TZ>`_ is True.
    
    .. seealso::
        
        The :class:`django_goodies.forms.TimeZoneField` form field.
