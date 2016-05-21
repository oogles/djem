=============
Other Goodies
=============

.. module:: django_goodies.misc

``AjaxResponse``
================

.. class:: AjaxResponse(request, data=None, success=None, **kwargs)
    
    .. versionadded:: 0.4
    
An extension of Django's ``JsonResponse`` that automatically adds any
messages in the `Django messages framework <https://docs.djangoproject.com/en/stable/ref/contrib/messages/>`_ store to the response body.

This allows views that are called via ``XMLHttpRequest`` requests, that simply return JSON-encoded raw data rather than a rendered template, to still make use of the messages framework and have those messages automatically embedded in the response and removed from the messages store.

The messages are added to the ``JsonResponse``'s ``data`` dictionary using the "messages" key. The messages themselves are dictionaries containing the following:

* message: The message string.
* tags: A string of the tags applied to the message, space separated.

If there are no messages to add, the "messages" key will not be added to the ``data`` dictionary at all (i.e. it will not be added as an empty list).

Using ``AjaxResponse`` differs from ``JsonResponse`` in the following ways:

* The first positional argument should be a Django ``HttpRequest`` instance. This argument is required - it is used to retrieve messages from the message framework store.
* The ``data`` argument is optional. If provided, it must always be a ``dict`` instance, and messages will be added to this dictionary. If not provided, messages will be added to a new ``dict`` instance, passing it to the parent ``JsonResponse``. Using the ``safe`` argument of ``JsonResponse`` to JSON-encode other types is not supported (see the `documentation <https://docs.djangoproject.com/en/stable/ref/request-response/#serializing-non-dictionary-objects>`_ for the ``safe`` argument of ``JsonResponse``).
* The optional argument ``success`` can be set to add a "success" attribute to the ``data`` dictionary. The "success" attribute will always be added as a boolean value, regardless of what was passed to the ``success`` argument. As with messages, this will be added to the ``data`` dictionary passed to the parent ``JsonResponse`` regardless of whether one was provided to ``AjaxResponse`` itself or not.

With the exception of ``safe``, as noted above, ``AjaxResponse`` accepts and supports all arguments of ``JsonResponse``.

Usage
-----

This simple example demontrates how ``AjaxResponse`` can be used with the messages framework:

.. code-block:: python
    
    from django.contrib import messages
    from django_goodies import AjaxResponse
    
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

A more complete example:

.. code-block:: python
    
    from django.contrib import messages
    from django_goodies import AjaxResponse
    
    def get_author_book_titles(request, author_id):
        
        try:
            author = Author.objects.get(pk=author_id)
        except Author.DoesNotExist:
            messages.error(request, 'Invalid author.')
            return AjaxResponse(request, success=False)
        
        titles = author.books.values_list('title', flat=True)
        
        return AjaxResponse(request, {'titles': titles}, success=True)
