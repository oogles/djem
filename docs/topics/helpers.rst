=======
Helpers
=======

.. module:: djem.misc

AjaxResponse
============

:class:`AjaxResponse` is an extension of Django's ``JsonResponse`` that automatically adds any messages in the `Django messages framework <https://docs.djangoproject.com/en/stable/ref/contrib/messages/>`_ store to the response body.

This allows views that are called via ``XMLHttpRequest`` requests, that simply return JSON-encoded raw data rather than a rendered template, to still make use of the messages framework and have those messages automatically embedded in the response and removed from the messages store.

The messages are added to the ``JsonResponse``'s ``data`` dictionary using the "messages" key. The messages themselves are dictionaries containing the following:

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
