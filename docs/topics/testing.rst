=======
Testing
=======

.. currentmodule:: djem.utils.tests

Djem includes some utilities that make writing certain types of tests easier. They are used internally within Djem's own test suite, but may well be useful elsewhere.


Test-only models
================

.. versionadded:: 0.7

It is often the case that tests are required for code that deals with models generically, and concrete example models to use in those tests may not exist. Django does not (yet) explicitly support defining models purely for testing. That is, models that do not get picked up by ``manage.py makemigrations`` or otherwise affect the live database, but only exist in the isolated test environment. But, thanks to the discussion on `Django ticket #7835 <https://code.djangoproject.com/ticket/7835>`_, the community has developed several workarounds.

Djem includes an adaption of one of the cleanest solutions (at time of writing, at least), `provided by Simon Charette <https://code.djangoproject.com/ticket/7835#comment:46>`_: :func:`setup_test_app`. It requires the use of a ``tests`` package, rather than just a ``test.py`` module, but otherwise all that is necessary is a simple function call.

Assuming a Django app with the name ``myapp``, simply place the following in ``myapp.tests.__init__``:

.. code-block:: python

    from djem.utils.tests import setup_test_app

    setup_test_app(__package__)

This will configure Django with an extra app, named ``myapp_tests``, and any models defined in ``myapp.tests.models`` will get picked up by the test database creation routine and added to the test database as part of this temporary app. These models can then be freely used in the test suite just like a regular model, but will not affect the live database.

If the default app label (created by appending ``_tests`` to the containing app's own app label) is not suitable, it can be provided explicitly:

.. code-block:: python

    from djem.utils.tests import setup_test_app

    setup_test_app(__package__, 'mytests')

.. warning::

    If the tests package, ``myapp.tests`` in the above examples, is imported by anything that forms part of the standard Django runtime environment (such as within a ``models.py`` module, or anything imported *by* a ``models.py`` module), the test-only models will **not** remain isolated to the test suite. It should not be necessary to import anything from within the test suite anywhere else in the project.


Enhanced request factory
========================

.. versionadded:: 0.6

The :class:`MessagingRequestFactory` is an extension of Django's ``RequestFactory`` `helper for tests <https://docs.djangoproject.com/en/stable/topics/testing/advanced/#the-request-factory>`_. It enables the use of the messages framework within the generated request.

This is typically not possible with ``RequestFactory``, since it does not execute middleware. While the `test client <https://docs.djangoproject.com/en/stable/topics/testing/tools/#the-test-client>`_ offers full middleware support, there are numerous situations in which ``RequestFactory`` is a preferable method of generating test requests.

:class:`MessagingRequestFactory` does not add full middleware support, but does prepare the generated requests such that the messages framework can be used. It does not use the standard message storage backend (as per the ``MESSAGE_STORAGE`` setting), but rather a memory-only backend that does not involve the use of sessions, cookies or any other means of persistent storage of the messages.

This means that messages need to be read in the same request they were added, or they will be lost. A subsequent request will not be able to access them as they typically would, e.g. after a redirect. Despite this limitation, it is sufficient in many testing scenarios - whether or not a message was added as part of a request can be tested, even if that message is inaccessible to a later request:

.. code-block:: python

    from django.contrib.auth.models import User
    from django.contrib import messages
    from django.test import TestCase

    from djem.utils.tests import MessagingRequestFactory

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


Rendering string-based templates
================================

.. versionadded:: 0.6

:class:`TemplateRendererMixin` is a mixin for ``TestCase`` classes whose tests render templates from strings (as opposed to rendering them from files), using the Django template engine. This can be helpful, for example, when testing templatetags. Short template snippets can be rendered to test the tag under a variety of scenarios without requiring separate template files for each.

The mixin adds a :meth:`~TemplateRendererMixin.render_template` method to the ``TestCase``. This method takes the template to be rendered, as a string, and a template context dictionary as arguments. It returns the rendered template.

.. code-block:: python

    from django.test import TestCase

    from djem.utils.tests import TemplateRendererMixin


    class SomeTestCase(TemplateRendererMixin, TestCase):

        def test_something(self):

            template_string = (
                '{% if something %}'
                '    <p>'
                '        RENDER THIS'
                '    </p>'
                '    <p>'
                '        AND THIS'
                '    </p>'
                '{% endif %}'
            )

            output = self.render_template(template_string, {
                'something': True
            })

            self.assertEqual(output, '<p> RENDER THIS </p><p> AND THIS </p>')

The output is stripped of all leading and trailing whitespace. Optionally, remaining whitespace will be "flattened" if the ``flatten`` argument is ``True``, which is the default. Flattening removes all whitespace from between HTML tags and compresses all other whitespace down to a single space.

Flattening makes comparing rendered template output easier. This is demonstrated in the above example. The following example shows the difference when ``flatten`` is given as ``False``:

.. code-block:: python

    def test_something(self):

        template_string = (
            '{% if something %}'
            '    <p>'
            '        RENDER THIS'
            '    </p>'
            '    <p>'
            '        AND THIS'
            '    </p>'
            '{% endif %}'
        )

        output = self.render_template(template_string, {
            'something': True
        }, flatten=False)

        self.assertEqual(output, '<p>        RENDER THIS    </p>    <p>        AND THIS    </p>')

:meth:`~TemplateRendererMixin.render_template` can optionally accept a ``request`` argument, which should be a ``HttpRequest`` instance if given. This enables it to be used to test templates that require being rendered with a ``RequestContext``. For example, it could be combined with the Django `request factory <https://docs.djangoproject.com/en/stable/topics/testing/advanced/#the-request-factory>`_:

.. code-block:: python

    from django.http import HttpResponse
    from django.test import RequestFactory, TestCase

    from djem.utils.tests import TemplateRendererMixin


    class SomeTestCase(TemplateRendererMixin, TestCase):

        def test_something(self):

            def view(r):

                template_string = '...'

                output = self.render_template(template_string, {}, r)

                return HttpResponse(output)

            request = RequestFactory().get('/test/')
            response = view(request)

            self.assertContains(response, '...', status_code=200)

If the ``TestCase`` has a ``user`` attribute, e.g. defined in ``setUp()`` to be available to all tests, a "user" variable will be added to the template context. This is done automatically unless ``request`` is provided.

.. code-block:: python

    from django.contrib.auth.models import User
    from django.test import TestCase

    from djem.utils.tests import TemplateRendererMixin


    class SomeTestCase(TemplateRendererMixin, TestCase):

        def setUp(self):

            self.user = self.user = User.objects.create_user(
                username='test.user', email='test@…', password='top_secret'
            )

        def test_something(self):

            template_string = '{{ user.username }}'

            output = self.render_template(template_string, {})

            self.assertEqual(output, 'test.user')
