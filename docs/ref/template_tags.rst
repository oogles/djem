=============
Template Tags
=============

.. module:: djem.templatetags.djem

Djem provides several template tags as part of the ``djem`` tag library.

Many of the tags are designed to help keep things `DRY <https://docs.djangoproject.com/en/stable/misc/design-philosophies/#don-t-repeat-yourself-dry>`_ and alleviate boilerplate code. The output of such tags is often dictated by a template, for which Djem will provide a default, but which can be overridden per-project using Django's standard `template overriding mechanism <https://docs.djangoproject.com/en/stable/howto/overriding-templates/>`_.


.. templatetag:: ifperm

``ifperm``
----------

The ``{% ifperm %}`` block tag performs an object-level permission check and, if that check *passes*, renders contents of the block. To perform the permission check, it requires a ``User`` instance, the name of the permission and a model instance. The check will pass if the given user has the given permission on the given instance.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifperm %}
    ...

The tag supports an ``else`` block, which will be rendered if the user does not have permission.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifperm user 'polls.vote_on_question' question_obj %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% else %}
        You do not have permission to vote on this question.
    {% endifperm %}
    ...


.. templatetag:: ifnotperm

``ifnotperm``
-------------

The ``{% ifnotperm %}`` block tag performs an object-level permission check and, if that check *fails*, the contents of the block are rendered. To perform the permission check, it requires a ``User`` instance, the name of the permission and a model instance. The check will fail if the given user *does not* have the given permission on the given instance.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% endifnotperm %}
    ...

The tag supports an ``else`` block, which will be rendered if the user does have permission.

.. code-block:: html+django

    {% load djem %}
    ...
    {% ifnotperm user 'polls.vote_on_question' question_obj %}
        You do not have permission to vote on this question.
    {% else %}
        <a href="{% url 'vote' question_obj.pk %}">Vote Now</a>
    {% endifnotperm %}
    ...


.. templatetag:: csrfify_ajax

``csrfify_ajax``
----------------

.. versionadded:: 0.6

The ``{% csrfify_ajax %}`` template tag renders a HTML ``<script>`` tag containing JavaScript to configure the ``X-CSRFToken`` header on outgoing AJAX requests where necessary (e.g. POST requests). The JavaScript is library-specific, and is stored in templates under ``djem/csrfify_ajax/``, e.g. ``djem/csrfify_ajax/jquery.html``.

Support for jQuery is included by default. Additional libraries can be added by creating project-specific templates for them under the ``djem/csrfify_ajax/`` path and providing the name of the template as an argument to the tag. Such templates have access to the CSRF token via the ``{{ csrf_token }}`` template variable.

.. code-block:: html+django

    {% load djem %}

    {# Uses jquery as default argument #}
    {% csrfify_ajax %}

    {# But it can be given explicitly #}
    {% csrfify_ajax 'jquery' %}

    {# As can another library, provided a template exists to support it #}
    {% csrfify_ajax 'some_other_lib' %}


.. templatetag:: paginate

``paginate``
------------

.. versionadded:: 0.6

The ``{% paginate %}`` template tag renders the pagination links associated with a result list. Simply pass it the same Django ``Page`` instance used to render the list itself and it will render appropriate page navigation links.

For example, where ``user_list`` is a ``Page`` instance:

.. code-block:: html+django

    {% load djem %}
    ...
    {% for user in user_list %}
        {{ user.name }}
    {% endfor %}
    {% paginate user_list %}
    ...

The structure of the navigation block that is rendered is controlled by the ``djem/pagination.html`` template.

.. seealso::

    :func:`~djem.pagination.get_page`
        A helper utility for retrieving a ``Page`` instance.


.. templatetag:: form_field

``form_field``
--------------

.. versionadded:: 0.6

The ``{% form_field %}`` template tag renders a form field in a consistent, customisable fashion. The structure of the output is controlled by the ``djem/form_field.html`` template. By default, it provides:

* A wrapping element with the following features:

    * By default, the element is a ``<div>``, but this can be modified using the :setting:`DJEM_FORM_FIELD_TAG` setting.
    * The element is given the following CSS classes:

        * ``form-field``
        * Any classes defined by the form, either `declaratively <https://docs.djangoproject.com/en/stable/ref/forms/api/#styling-required-or-erroneous-form-rows>`_ or `programatically <https://docs.djangoproject.com/en/stable/ref/forms/api/#django.forms.BoundField.css_classes>`_.
        * Any classes passed to the template tag.

    * The element is given additional HTML attributes based on keyword arguments passed to the template tag.

* The field's label.
* The field's error list (when applicable). The error list is the Django default ``<ul class="errorlist">``.
* The field itself.
* A ``<div>`` with the CSS class ``form-field__help`` containing the field's help text, if any.

.. code-block:: html+django

    {% load djem %}
    ...
    {# Basic usage #}
    {% form_field form.first_name %}

    {# Adding extra CSS classes to the wrapper #}
    {% form_field form.first_name 'one-half' %}
    {% form_field form.last_name 'one-half' %}

    {# Adding extra HTML attributes to the wrapper #}
    {% url 'verify-email' as verify_email_url %}
    {% form_field form.email data_url=verify_email_url %}
    ...

.. note::

    Since attribute names can contain dashes, which are invalid in Python keyword argument names, any underscores in the argument name will be converted into dashes to form the HTML attribute name.

.. templatetag:: checkbox

``checkbox``
------------

.. versionadded:: 0.6

The ``{% checkbox %}`` template tag is very similar to the ``{% form_field %}`` tag. It likewise renders form fields, and the same ``djem/form_field.html`` template controls the output, but it is specifically designed for checkboxes. The differences lie in the way the field's ``<label>`` element is rendered:

* it is included *after* the field itself, not before
* it is given the ``check-label`` CSS class, allowing it to be styled independently of regular labels

Also, unlike ``{% form_field %}``, ``{% checkbox %}`` is a *block tag*. It uses the content between its start and end tags as the label for the field. Specifically, this allows HTML to be included in the label text:

.. code-block:: html+django

    {% load djem %}
    ...
    {% checkbox form.terms %}
        I agree to the <a href="{% url 'terms' %}" target="_blank">Terms of Service</a>.
    {% endcheckbox %}
    ...

If no content is entered between the start and end tags, the field's default label text is used. In this case, the ``<label>`` element will still be included after the field itself, instead of before, and will still receive the ``check-label`` class.

.. note::

    Don't go too crazy with HTML in the label text. It is still rendered inside a ``<label>`` element, so should only contain markup that is valid within ``<label>``.

.. note::

    ``{% checkbox %}`` is not strictly limited to actual checkbox inputs. You could, if for some reason it was appropriate, use it for any form field.
