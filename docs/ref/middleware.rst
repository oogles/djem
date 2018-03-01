==========
Middleware
==========

.. module:: djem.middleware

``MessageMiddleware``
=====================

.. class:: MessageMiddleware

    .. versionadded:: 0.6

    Middleware that handles temporary messages, differentiating between those added as part of an AJAX request vs those that are not. Different storage backends are used for each: the default backend (configurable via ``MESSAGE_STORAGE``) for standard requests and a custom memory-only backend for AJAX requests.

    Using a memory-only backend, which does not offer any persistence between requests, prevents simultaneous AJAX requests interfering with each other's message stores, avoiding the `documented caveat <https://docs.djangoproject.com/en/stable/ref/contrib/messages/#behavior-of-parallel-requests>`_ of Django's out-of-the-box messages framework.

    This is a drop-in replacement for Django's own ``MessageMiddleware``:

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

.. important::

    ``MessageMiddleware`` uses the ``HttpRequest`` object's ``is_ajax()`` method to differentiate between AJAX and non-AJAX requests. An ``XMLHttpRequest`` call must `use the appropriate headers <https://docs.djangoproject.com/en/stable/ref/request-response/#django.http.HttpRequest.is_ajax>`_ in order to be correctly detected.

.. seealso::

    :class:`~djem.ajax.AjaxResponse`
        An extension of Django's ``JsonResponse`` that, among other things, will automatically include any messages that are in the message store as part of the response.
