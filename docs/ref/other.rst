=============
Other Goodies
=============

.. module:: djem.misc

``AjaxResponse``
================

.. class:: AjaxResponse(request, data=None, success=None, **kwargs)

    .. versionadded:: 0.4

    An extension of Django's ``JsonResponse``, differing in the following ways:

    * The ``data`` argument is optional. If provided, it must always be a ``dict`` instance. If not provided, a new ``dict`` instance will be created and used. Using the ``safe`` argument of ``JsonResponse`` to JSON-encode other types is not supported (see the `documentation <https://docs.djangoproject.com/en/stable/ref/request-response/#serializing-non-dictionary-objects>`_ for the ``safe`` argument of ``JsonResponse``).
    * The first positional argument should be a Django ``HttpRequest`` instance, used to retrieve messages from the `Django message framework <https://docs.djangoproject.com/en/stable/ref/contrib/messages/>`_ store and add them to the ``data`` dictionary under the "messages" key. The messages are added as a list of dictionaries containing:

        * message: The message string.
        * tags: A string of the tags applied to the message, space separated.

    * The optional argument ``success`` can be set to add a "success" key to the ``data`` dictionary. The "success" key will always be added as a boolean value, regardless of what was passed (though it will not be added at all if nothing was passed).

    With the exception of ``safe``, as noted above, ``AjaxResponse`` accepts and supports all arguments of ``JsonResponse``.
