import warnings

from django import forms


class UserSavable:
    """
    A mixin for a Django ``ModelForm`` that adds support for models using the
    :class:`~djem.models.Auditable` model mixin. It handles providing a user
    instance to the model's ``save()`` method when the form's own ``save()``
    method is called, as is required by :class:`~djem.models.Auditable`.
    
    This mixin *assumes* the presence of a ``self.user`` attribute that the
    ``save()`` method can use. It is designed for use by forms that already
    accept and store a known user, e.g. as a constructor argument.
    
    For a form that provides the same customisation of the ``save()`` method
    and includes ``user`` as a constructor argument, see :class:`AuditableForm`.
    """
    
    def save(self, commit=True):
        
        # Call super.save() with commit=False so .save() can be called on the
        # instance with the required user argument
        instance = super().save(commit=False)
        
        if commit:
            instance.save(self.user)
            self.save_m2m()
            del self.save_m2m  # pretend commit=False was never used
        
        return instance


class AuditableForm(UserSavable, forms.ModelForm):
    """
    A Django ``ModelForm`` that is customised to support models using the
    :class:`~djem.models.Auditable` model mixin. It handles providing a user
    instance to the model's ``save()`` method when the form's own ``save()``
    method is called, as is required by :class:`~djem.models.Auditable`. It
    also adds a ``user`` keyword argument to the constructor so the ``save()``
    method has a known user to work with. The ``user`` argument is required if
    the field is bound, otherwise it is optional. The given user is stored in
    the :attr:`~AuditableForm.user` instance attribute. Subclasses may choose
    to use the known user for their own purposes.
    
    For a mixin that provides the same customisation of the ``save()`` method
    without the extra constructor argument (e.g. for use by forms that already
    accept and store a known user), see :class:`UserSavable`.
    """
    
    def __init__(self, *args, user=None, **kwargs):
        
        super().__init__(*args, **kwargs)
        
        # User is required for bound forms
        if self.is_bound and not user:
            raise TypeError('Bound {0} instances require a "user" argument.'.format(self.__class__.__name__))
        
        # Set self.user regardless of whether or not the form is bound. Child
        # forms may well require the user when the form is unbound as well.
        self.user = user


# Backwards compat.
# TODO: Remove in 1.0
class CommonInfoForm(AuditableForm):
    
    def __init__(self, *args, **kwargs):
        
        warnings.warn('Use of CommonInfoForm is deprecated, use AuditableForm instead.', DeprecationWarning)
        
        super().__init__(*args, **kwargs)
