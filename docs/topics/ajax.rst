====
AJAX
====

AJAX and CSRF
=============

.. currentmodule:: djem.templatetags.djem

As `Django notes in its own documentation <https://docs.djangoproject.com/en/stable/ref/csrf/#ajax>`_, adding the CSRF token to AJAX POST requests can be done on each individual request, or you can use JavaScript framework features to add it to all outgoing POST requests, using the ``X-CSRFToken`` header.

Djem's :ttag:`csrfify_ajax` template tag does exactly that in a single line:

.. code-block:: html+django

    {% load djem %}
    ...
    {% csrfify_ajax %}
    ...

The tag injects a ``<script>`` tag containing library-specific code to add ``X-CSRFToken`` headers to all outgoing requests that require it.

.. note::

    As with Django's standard ``{% csrf_token %}`` tag, to use ``{% csrfify_ajax %}`` the view must use ``RequestContext`` to render the template, e.g. using the ``render()`` shortcut function.

.. note::

    As the ``<script>`` tag rendered by the tag contains library-specific code, it needs to be included *after* the library itself.

Library support
---------------

By default, Djem ships with support for jQuery, but it is simple to add additional libraries. Extra libraries may be included by default in future releases.

The ``<script>`` tag, and its contents, that :ttag:`csrfify_ajax` renders is stored in a template under the ``djem/csrfify_ajax/`` directory, named after the library. E.g. the included jQuery template is at ``djem/csrfify_ajax/jquery.html``. As with any Django app templates, you can override those that Djem includes or add your own by including your own ``djem/csrfify_ajax/`` directory somewhere on your configured template path. See the `Django documentation for overriding templates <https://docs.djangoproject.com/en/stable/howto/overriding-templates/>`_.

By providing your own template, you can use :ttag:`csrfify_ajax` with any library of your choosing. To specify which library template the tag should use, simply provide the name of the template (without the ``.html``) as an argument:

.. code-block:: html+django

    {% load djem %}
    ...
    {% csrfify_ajax 'some_other_lib' %}
    ...

A default value of ``'jquery'`` is used when no argument is provided.


Responding to requests
======================

.. currentmodule:: djem.ajax

Django provides ``JsonResponse`` to aid in responding to data-centric AJAX requests (as opposed to those that return rendered HTML to be injected directly into the page). Djem provides a simple extension of ``JsonResponse`` that adds some additional features: :class:`AjaxResponse`.

``AjaxResponse`` automatically adds any messages in the `Django messages framework <https://docs.djangoproject.com/en/stable/ref/contrib/messages/>`_ store to the response body.

This allows views that are called via AJAX and return JSON-encoded data to still make use of the messages framework and have those messages automatically embedded in the response and removed from the message store.

The messages are added to the parent ``JsonResponse``'s ``data`` dictionary using the "messages" key. The messages themselves are dictionaries containing the following:

* message: The message string.
* tags: A string of the tags applied to the message, space separated.

If there are no messages to add, the "messages" key will not be added to the ``data`` dictionary at all (i.e. it will not be added as an empty list).

Using :class:`AjaxResponse` differs from ``JsonResponse`` in the following ways:

* The first positional argument should be a Django ``HttpRequest`` instance. This argument is required - it is used to retrieve messages from the message framework store.
* The ``data`` argument is optional. If provided, it must always be a ``dict`` instance, and messages will be added to this dictionary. If not provided, messages will be added to a new ``dict`` instance, passing it to the parent ``JsonResponse``. Using the ``safe`` argument of ``JsonResponse`` to JSON-encode other types is not supported (see the `documentation <https://docs.djangoproject.com/en/stable/ref/request-response/#serializing-non-dictionary-objects>`_ for the ``safe`` argument of ``JsonResponse``).
* The optional argument ``success`` can be set to add a "success" attribute to the ``data`` dictionary. The "success" attribute will always be added as a boolean value, regardless of what was passed to the ``success`` argument (though it will not be added at all if nothing was passed). As with messages, this will be added to the ``data`` dictionary passed to the parent ``JsonResponse`` regardless of whether one was provided to :class:`AjaxResponse` itself or not.

With the exception of ``safe``, as noted above, :class:`AjaxResponse` accepts and supports all arguments of ``JsonResponse``.

Usage
-----

This simple example demontrates how :class:`AjaxResponse` can be used with the messages framework:

.. code-block:: python

    from django.contrib import messages
    from djem import AjaxResponse

    def my_view(request):

        # do something...

        messages.success(request, 'Did something!')

        return AjaxResponse(request)

This will give a JSON-encoded response body that looks like this:

.. code-block:: python

    {
        "messages":[{
            "message":"Did something!",
            "tags":"success"
        }]
    }

The following is a more complete example, based on the "polls" application created `in the Django tutorial <https://docs.djangoproject.com/en/stable/intro/tutorial01/>`_. This view records a vote on a given ``Choice``:

.. code-block:: python

    from django.contrib import messages
    from djem import AjaxResponse

    from polls.models import Choice

    def vote_on_question(request, choice_id):

        try:
            choice = Choice.objects.get(pk=choice_id)
        except Choice.DoesNotExist:
            messages.error(request, 'Invalid choice.')
            return AjaxResponse(request, success=False)

        choice.votes += 1
        choice.save()

        messages.success(request, 'Vote recorded.')

        return AjaxResponse(request, {'votes': choice.votes}, success=True)
