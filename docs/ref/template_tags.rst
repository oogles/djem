=============
Template Tags
=============

.. module:: djem.templatetags.djem

Djem provides several template tags as part of the ``djem`` tag library.

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

Support for jQuery is included by default. Additional libraries can be added by creating project-specific templates for them under the ``djem/csrfify_ajax/`` path and providing the name of the template as an argument to the tag.

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

The ``{% paginate %}`` template tag helps keep things `DRY <https://docs.djangoproject.com/en/stable/misc/design-philosophies/#don-t-repeat-yourself-dry>`_ and alleviate the boilerplate around defining the pagination links associated with a result list. Simply pass it the same Django ``Page`` instance used to render the list itself and it will render appropriate page navigation links.

For example, where ``user_list`` is a ``Page`` instance:

.. code-block:: html+django

    {% load djem %}
    ...
    {% for user in user_list %}
        {{ user.name }}
    {% endfor %}
    {% paginate user_list %}
    ...

The structure of the navigation block that is rendered is controlled by the ``djem/pagination.html`` template. Djem's default can be overridden per-project `as per any Django app template <https://docs.djangoproject.com/en/stable/howto/overriding-templates/>`_

.. seealso::

    :func:`~djem.pagination.get_page`
        A helper utility for retrieving a ``Page`` instance.
