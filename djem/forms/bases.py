from django import forms


class CommonInfoForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        
        user = kwargs.pop('user', None)
        
        super(CommonInfoForm, self).__init__(*args, **kwargs)
        
        # User is required for bound forms
        if self.is_bound and not user:
            raise TypeError('Bound {0} instances require a "user" argument.'.format(self.__class__.__name__))
        
        # Set self.user regardless of whether or not the form is bound. Child
        # forms may well require the user when the form is unbound as well.
        self.user = user
    
    def save(self, commit=True):
        
        # Call super.save() with commit=False so .save() can be called on the
        # instance with the required user argument
        instance = super(CommonInfoForm, self).save(commit=False)
        
        if commit:
            instance.save(self.user)
            self.save_m2m()
            del self.save_m2m  # pretend commit=False was never used
        
        return instance
