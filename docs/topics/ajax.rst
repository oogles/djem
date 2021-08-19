====
AJAX
====

Checking authentication
=======================

.. currentmodule:: djem.ajax

Django's built in ``login_required()`` decorator is not well suited to AJAX requests. If the user making the request is not authenticated, it issues a redirect to the configured login view. This is not particularly useful to an AJAX client.

Djem provides a simple alternate decorator, :func:`ajax_login_required`, to use on views that are the target of AJAX requests. Instead of issuing a redirect if the user is not authenticated, it returns a ``HttpForbiddenResponse``.

.. versionadded:: 0.7

    The :func:`ajax_login_required` decorator.


Responding to AJAX requests
===========================

.. currentmodule:: djem.ajax

Django provides ``JsonResponse`` to aid in responding to data-centric AJAX requests (as opposed to those that return rendered HTML to be injected directly into the page). Djem provides a simple extension of ``JsonResponse`` that adds some additional features: :class:`AjaxResponse`.

:class:`AjaxResponse` automatically adds any messages in the `Django messages framework <https://docs.djangoproject.com/en/stable/ref/contrib/messages/>`_ store to the response body.

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

This simple example demonstrates how :class:`AjaxResponse` can be used with the messages framework:

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

.. note::

    This example is for illustrative purposes only. It does not represent a good way to increment a counter in the database - such an operation `should be performed atomically <https://docs.djangoproject.com/en/stable/ref/models/expressions/#f-expressions>`_.

CSRF
====

.. currentmodule:: djem.templatetags.djem

As `Django notes in its own documentation <https://docs.djangoproject.com/en/stable/ref/csrf/#ajax>`_, adding the CSRF token to AJAX POST requests can be done on each individual request, or you can use JavaScript framework features to add it to all outgoing POST requests, using the ``X-CSRFToken`` header.

Djem's :ttag:`csrfify_ajax` template tag does exactly that in a single line:

.. code-block:: html+django

    {% load djem %}
    ...
    {% csrfify_ajax %}
    ...

The tag injects a ``<script>`` tag containing library-specific code to add ``X-CSRFToken`` headers to all outgoing requests that require it.

.. versionadded:: 0.6
    The :ttag:`csrfify_ajax` template tag.

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

These templates have access to the CSRF token via the ``{{ csrf_token }}`` template variable.


XSS
===

.. currentmodule:: djem.ajax

Django's template system `automatically escapes all template variables by default <https://docs.djangoproject.com/en/stable/ref/templates/language/#automatic-html-escaping>`_. This helps prevent user-generated content from messing up the rendered HTML, or worse, exposing your users to a security vulnerability. This kind of injection is known as `cross site scripting <https://docs.djangoproject.com/en/stable/topics/security/#cross-site-scripting-xss-protection>`_ or XSS.

If including user-generated content in the JSON body of an AJAX response (that is, not returning rendered HTML), these autoescaping protections do not apply. If that content is then injected directly into the page when the response is received, similar XSS vulnerabilities exist.

You should be wary of XSS threats when returning data in this way. Either ensure all returned data has been properly escaped on the server side, or do not inject it as HTML (e.g. use jQuery's `.text() method instead of .html() <http://api.jquery.com/text/>`_)

Djem's :class:`AjaxResponse` class helps mitigate one potential vector for XSS - messages added via the Django messages framework. All messages included in the response body are escaped, unless `marked as safe <https://docs.djangoproject.com/en/stable/ref/utils/#module-django.utils.safestring>`_.

.. code-block:: python

    # View
    from django.contrib import messages
    from django.template.defaultfilters import mark_safe
    from djem.ajax import AjaxResponse

    def view(request):

        some_user_input = '<strong>BAD</strong> user input'

        messages.error(request, 'Invalid input: {0}.'.format(some_user_input))
        messages.info(request, mark_safe('This is a message with <em>safe</em> HTML.'))

        return AjaxResponse(request)

    # Response Body
    {
        "messages": [{
            "message": "Invalid input: &lt;strong&gt;BAD&lt;/strong&gt; user input.",
            "tags": "error"
        }, {
            "message": "This is a message with <em>safe</em> HTML.",
            "tags": "info"
        }]
    }


The messages framework
======================

.. currentmodule:: djem.ajax

As noted above, the :class:`AjaxResponse` class can automatically include messages stored in Django's `builtin messages framework <https://docs.djangoproject.com/en/stable/ref/contrib/messages/>`_. But whether or not you are using :class:`AjaxResponse`, the messages framework is not perfectly suited for use in AJAX requests.

It is designed to make it simple to store one-time notification messages throughout the lifecycle of a request, then display them together at some later point, typically when rendering a template. Importantly, it offers persistent storage of these messages, allowing them to be retrieved and displayed on a *later* request. This is particularly useful when issuing browser redirects to display subsequent pages, and needing the messages from the current request to be available after the redirect.

As Django `notes in its documentation <https://docs.djangoproject.com/en/stable/ref/contrib/messages/#behavior-of-parallel-requests>`_, this persistence between requests can cause issues if multiple requests are issued in parallel. The wrong request can read from the persistent messages store, display the messages in the wrong context, and prevent the messages being shown where they were intended. When dealing with full requests for entire pages, this situation only occurs when a user is issuing requests from multiple browser tabs/windows at the same time, and thus is only a minor problem. But on a site using AJAX requests, the risk increases. Depending on the nature of the site and the AJAX requests it issues, the chances of multiple requests running simultaneously can increase dramatically, making the problem of requests stealing messages from one another much worse.

One solution is to avoid using the messages framework in views used by AJAX requests. After all, an AJAX request doesn't require the same redirect hopping that might otherwise be required - any messages that it generates can be returned immediately, making the persistent storage offered by the framework unnecessary. But some views can be used by both AJAX and non-AJAX requests, plus a consistent method of handling message passing regardless of the view would be nice.

.. currentmodule:: djem.middleware

Djem provides a :class:`MessageMiddleware` class that acts as a drop-in replacement for Django's own. Simply replace the ``django.contrib.messages.middleware.MessageMiddleware`` string in your ``MIDDLEWARE`` setting with ``djem.middleware.MessageMiddleware``.

.. code-block:: python

    # before
    MIDDLEWARE = [
        ...
        'django.contrib.messages.middleware.MessageMiddleware'
        ...
    ]

    # after
    MIDDLEWARE = [
        ...
        'djem.middleware.MessageMiddleware'
        ...
    ]

Djem's :class:`MessageMiddleware` is nearly identical to Django's, and usage of the messages framework itself is completely unchanged. The middleware has only one minor difference: it disables persistent message storage for AJAX requests. On standard requests, the storage backend configured via the ``MESSAGE_STORAGE`` setting is still used as per usual. But on AJAX requests, a separate storage backend is used - one that keeps the messages in memory only, making them inaccessible to simultaneous requests.

.. versionadded:: 0.6
    :class:`MessageMiddleware`

.. important::

    :class:`MessageMiddleware` uses the ``HttpRequest`` object's ``is_ajax()`` method to differentiate between AJAX and non-AJAX requests. Your ``XMLHttpRequest`` call must `use the appropriate headers <https://docs.djangoproject.com/en/stable/ref/request-response/#django.http.HttpRequest.is_ajax>`_ in order to be correctly detected. Most modern JavaScript libraries do so.

.. note::

    Using a memory-only storage backend for messages in AJAX requests also makes them unavailable to subsequent requests. If using Djem's :class:`MessageMiddleware`, be sure to read the messages from the storage as part of the same request and include them in the response. :class:`~djem.ajax.AjaxResponse` does this automatically.

.. note::

    Using Djem's :class:`MessageMiddleware` doesn't change any of the other requirements for using the messages framework. For instance, ``django.contrib.messages`` still needs to be listed in the ``INSTALLED_APPS`` setting and, if using ``SessionStorage``, ``SessionMiddleware`` still needs to be listed before ``MessageMiddleware`` in the ``MIDDLEWARE`` setting.

