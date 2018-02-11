========
Messages
========

In addition to :ref:`middleware that makes the use of the Django messages framework from within AJAX requests safer <ajax-messages>`, Djem provides some other helpful utils around messaging.

Enhanced request factory
========================

.. versionadded:: 0.6

.. currentmodule:: djem.utils.messages

The :class:`MessagingRequestFactory` is an extension of Django's ``RequestFactory`` `helper for tests <https://docs.djangoproject.com/en/stable/topics/testing/advanced/#the-request-factory>`_. It enables the use of the messages framework within the generated request.

This is typically not possible with ``RequestFactory``, since it does not execute middleware. While the `test client <https://docs.djangoproject.com/en/stable/topics/testing/tools/#the-test-client>`_ offers full middleware support, there are numerous situations in which ``RequestFactory`` is a preferable method of generating test requests.

:class:`MessagingRequestFactory` does not add full middleware support, but does prepare the generated requests such that the messages framework can be used. It does not use the standard message storage backend (as per the ``MESSAGE_STORAGE`` setting), but rather a memory-only backend that does not involve the use of sessions, cookies or any other means of persistent storage of the messages.

This means that messages need to be read in the same request they were added, or they will be lost. A subsequent request will not be able to access them as they typically would, e.g. after a redirect. Despite this limitation, it is sufficient in many testing scenarios - whether or not a message was added as part of a request can be tested, even if that message is inaccessible to a later request:

.. code-block:: python

    from django.contrib.auth.models import User
    from django.contrib import messages
    from django.test import TestCase

    from djem.utils.messages import MessagingRequestFactory

    # Views expected to set messages
    from .views import MyView, my_view


    class SimpleTest(TestCase):

        def setUp(self):

            self.factory = MessagingRequestFactory()
            self.user = User.objects.create_user(
                username='test.user', email='test@…', password='top_secret'
            )

        def test_details(self):

            request = self.factory.get('/customer/details')

            # Recall that middleware are not supported. You can simulate a
            # logged-in user by setting request.user manually.
            request.user = self.user

            # Test my_view() as if it were deployed at /customer/details
            response = my_view(request)

            # Use this syntax for class-based views
            response = MyView.as_view()(request)

            self.assertEqual(response.status_code, 200)

            # Test the expected message was set
            message_list = list(messages.get_messages(request))
            self.assertEqual(len(message_list), 1)
            self.assertEqual(message_list[0].message, 'An error occurred.')
