===============
Rendering Forms
===============

.. versionadded:: 0.6

.. currentmodule:: djem.templatetags.djem

Djem provides some simple template tags to assist in rendering form fields in templates.

While Django provides numerous ways to customise the way it renders form fields, they are often inadequate. The options for `rendering all of a form's fields <https://docs.djangoproject.com/en/stable/topics/forms/#form-rendering-options>`_ as a series of ``<tr>``, ``<li>``, or ``<p>`` tags, are limited to providing fairly basic field/label pairs, with little opportunity for customisation. And `rendering fields manually <https://docs.djangoproject.com/en/stable/topics/forms/#rendering-fields-manually>`_ often results in repeating boilerplate code, e.g. specifying a wrapping element, the field, its label, its error list, etc.

The :ttag:`form_field` and :ttag:`checkbox` template tags use a fully customisable template to render each individual field. The template, found at ``djem/form_field.html``, can be altered per-project using Django's standard `template overriding mechanism <https://docs.djangoproject.com/en/stable/howto/overriding-templates/>`_. By default, it provides:

* A wrapping element with the following features:

    * By default, the element is a ``<div>``, but this can be modified using the :setting:`DJEM_FORM_FIELD_TAG` setting.
    * The element is given the following CSS classes:

        * ``form-field``
        * Any classes defined by the form. See below examples.
        * Any classes passed to the template tag. See below examples.

    * The element is given additional HTML attributes based on keyword arguments passed to the template tag. See below examples.

* The field's label (for fields rendered with ``form_field``, see below examples).
* The field's error list (when applicable). The error list is the Django default ``<ul class="errorlist">``.
* The field itself.
* The specified checkbox label (for fields rendered with ``checkbox``, see below examples). This ``<label>`` element will have the ``check-label`` CSS class.
* A ``<div>`` with the CSS class ``form-field__help`` containing the field's help text, if any.

The following usage examples are based off a basic user registration form:

.. code-block:: python

    from django import forms

    class RegistrationForm(forms.Form):
        first_name = forms.CharField(label='Your first name')
        last_name = forms.CharField(label='Your last name')
        email = forms.EmailField(label='Your email address', help_text="Don't worry, we won't share your email address with anyone.")
        terms = forms.BooleanField(label='Terms of Service')

In the below template snippets, an instance of this form is contained in a context variable called ``registration_form``.

``form_field``
==============

The :ttag:`form_field` tag has a single required argument: the form field to be rendered.

.. code-block:: html+django

    {% load djem %}
    ...
    {% form_field registration_form.first_name %}
    {% form_field registration_form.last_name %}
    {% form_field registration_form.email %}
    {% form_field registration_form.terms %}
    ...

Rendering this template would result in the following HTML:

.. code-block:: html

    <div class="form-field">
        <label for="id_first_name">Your first name:</label>
        <input type="text" name="first_name" id="id_first_name" />
    </div>
    <div class="form-field">
        <label for="id_last_name">Your last name:</label>
        <input type="text" name="last_name" id="id_last_name" />
    </div>
    <div class="form-field">
        <label for="id_email">Your email address:</label>
        <input type="email" name="email" id="id_email" />
        <div class="form-field__help">Don't worry, we won't share your email address with anyone.</div>
    </div>
    <div class="form-field">
        <label for="id_terms">Terms of Service:</label>
        <input type="checkbox" name="terms" id="id_terms" />
    </div>

This doesn't look too different from what ``{{ registration_form.as_p }}`` would generate, but note:

* The ``<div>`` wrapper around each field can be customised without even overriding the template, using the :setting:`DJEM_FORM_FIELD_TAG` setting.
* The ``form-field`` class provides an easy CSS styling target.
* Help text is rendered automatically when defined, with its own easily targetted ``field-field__help`` class for styling.
* The entire block rendered for each field can be completely customised by overriding the ``djem/form_field.html`` template, allowing for custom and consistent rendering of form fields across your project.

The :ttag:`form_field` tag has more advanced uses, too. But first, the "terms" checkbox rendered above could be nicer, and that's what the :ttag:`checkbox` tag is for.

``checkbox``
============

The :ttag:`checkbox` tag uses the same ``djem/form_field.html`` template as :ttag:`form_field`, but it renders labels differently:

* it includes the ``<label>`` element *after* the field itself, not before
* it gives the ``<label>`` element the ``check-label`` CSS class, allowing it to be styled independently of regular labels

Also, unlike :ttag:`form_field`, :ttag:`checkbox` is a *block tag*. It uses the content between its start and end tags as the label for the field. This has one important benefit: we can include HTML in the label text. Updating the previous example to use the :ttag:`checkbox` tag for the "terms" field:

.. code-block:: html+django

    {% load djem %}
    ...
    {% checkbox registration_form.terms %}
        I agree to the <a href="{% url 'terms' %}" target="_blank">Terms of Service</a>.
    {% endcheckbox %}
    ...

The rendered HTML for this field then becomes:

.. code-block:: html

    <div class="form-field">
        <input type="checkbox" name="terms" id="id_terms" />
        <label class="check-label" for="id_terms">I agree to the <a href="{% url 'terms' %}" target="_blank">Terms of Service</a>.</label>
    </div>

That's a bit more user-friendly.

If no content is entered between the start and end tags, the field's default label text is used. In this case, the ``<label>`` element will still be included after the field itself, instead of before, and will still receive the ``check-label`` class.

.. note::

    Don't go too crazy with HTML in your label text. It is still rendered inside a ``<label>`` element, so should only contain markup that is valid within ``<label>``.

.. note::

    :ttag:`checkbox` is not strictly limited to actual checkbox inputs. You could, if for some reason it was appropriate, use it for any form field.

Extra CSS classes
=================

Both :ttag:`form_field` and :ttag:`checkbox` can add additional field-specific CSS classes to the wrapping element. These classes can come from two places: the ``Form`` class definition, or passing them into the template tag itself.

A ``Form`` class can specify additional CSS classes per field in several ways. The ``error_css_class`` and ``required_css_class`` `attributes can be used <https://docs.djangoproject.com/en/stable/ref/forms/api/#styling-required-or-erroneous-form-rows>`_ to automatically apply additional classes to fields that are required or contain errors, respectively. Also, custom classes can be `applied to specific fields <https://docs.djangoproject.com/en/stable/ref/forms/api/#django.forms.BoundField.css_classes>`_ using their ``css_classes()`` method.

Adapting the registration form example to add a CSS class to highlight required fields is simple:

.. code-block:: python

    from django import forms

    class RegistrationForm(forms.Form):

        required_css_class = 'form-field--required'

        first_name = forms.CharField(label='Your first name')
        last_name = forms.CharField(label='Your last name')
        email = forms.EmailField(label='Your email address', help_text="Don't worry, we won't share your email address with anyone.")
        terms = forms.BooleanField(label='Terms of Service')

Without changing the template, this generates the following HTML:

.. code-block:: html

    <div class="form-field  form-field--required">
        <label for="id_first_name">Your first name:</label>
        <input type="text" name="first_name" id="id_first_name" />
    </div>
    <div class="form-field  form-field--required">
        <label for="id_last_name">Your last name:</label>
        <input type="text" name="last_name" id="id_last_name" />
    </div>
    <div class="form-field  form-field--required">
        <label for="id_email">Your email address:</label>
        <input type="email" name="email" id="id_email" />
        <div class="form-field__help">Don't worry, we won't share your email address with anyone.</div>
    </div>
    <div class="form-field  form-field--required">
        <label for="id_terms">Terms of Service:</label>
        <input type="checkbox" name="terms" id="id_terms" />
    </div>

The other way to apply custom CSS classes to a field is to pass them directly into the template tag. For example, in order to display the ``first_name`` and ``last_name`` fields side-by-side, simply pass in a CSS class that can style them accordingly:

.. code-block:: html+django

    {% load djem %}
    ...
    {% form_field registration_form.first_name 'one-half' %}
    {% form_field registration_form.last_name 'one-half' %}
    {% form_field registration_form.email %}
    {% form_field registration_form.terms %}
    ...

.. code-block:: html

    <div class="form-field  form-field--required  one-half">
        <label for="id_first_name">Your first name:</label>
        <input type="text" name="first_name" id="id_first_name" />
    </div>
    <div class="form-field  form-field--required  one-half">
        <label for="id_last_name">Your last name:</label>
        <input type="text" name="last_name" id="id_last_name" />
    </div>
    <div class="form-field  form-field--required">
        <label for="id_email">Your email address:</label>
        <input type="email" name="email" id="id_email" />
        <div class="form-field__help">Don't worry, we won't share your email address with anyone.</div>
    </div>
    <div class="form-field  form-field--required">
        <label for="id_terms">Terms of Service:</label>
        <input type="checkbox" name="terms" id="id_terms" />
    </div>

Extra HTML attributes
=====================

:ttag:`form_field` and :ttag:`checkbox` also support adding custom HTML attributes to the wrapping element. The attribute name and value can be provided to the template tag as keyword arguments. Since attribute names can contain dashes, which are invalid in Python keyword argument names, any underscores in the argument name will be converted into dashes to form the HTML attribute name.

This feature is probably most useful for attaching ``data-*`` attributes. For example, if interacting with a particular field should trigger an AJAX lookup of some description, the URL to use for that request could be stored in a ``data-url`` attribute:

.. code-block:: html+django

    {% load djem %}
    ...
    {% url 'verify-email' as verify_email_url %}
    {% form_field registration_form.email data_url=verify_email_url %}
    ...

.. code-block:: html

    <div class="form-field  form-field--required" data-url="/accounts/email/verify/">
        <label for="id_email">Your email address:</label>
        <input type="email" name="email" id="id_email" />
        <div class="form-field__help">Don't worry, we won't share your email address with anyone.</div>
    </div>

Something like the above could be used, for example, to keep hardcoded values (such as URLs) out of external JavaScript files.

Rendering in bulk
=================

If you don't need per-field customisation, such as additional CSS classes, extra HTML attributes, or custom checkbox labels, you can use :ttag:`form_field` in a loop:

.. code-block:: html+django

    {% load djem %}
    ...
    {% for field in form.hidden_fields %}
        {{ field }}
    {% endfor %}

    {% for field in form.visible_fields %}
        {% form_field field %}
    {% endfor %}
    ...

.. note::

    Note that, while :ttag:`form_field` will work for hidden fields, it is largely useless. Most of the features it provides are unnecessary for hidden fields.
