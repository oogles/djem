==========
Pagination
==========

Djem provides some simple helpers to remove common boilerplate in fetching and rendering pages of results among some list of items.

In the view
===========

.. currentmodule:: djem.pagination

Django's ``Page`` object provides a number of helpful methods and attributes that aid in rendering a paged result list, in addition to providing a slice of the result list itself. However, obtaining a ``Page`` instance can involve a bit of boilerplate, particularly in validating the page number and handling various possible invalid states. Moreover, it needs to be repeated in every view that uses pagination.

Djem's :func:`get_page` removes this boilerplate. It is a basic wrapper around a Django ``Paginator`` object that primarily provides some sanity checking of the given page number.

Internally, it constructs a ``Paginator`` instance and uses its ``page()`` method to retrieve a ``Page``.

See the Django `pagination documentation <https://docs.djangoproject.com/en/stable/topics/pagination/>`_ for details on the ``Paginator`` and ``Page`` objects provided by Django.

.. versionadded:: 0.5

Usage
-----

:func:`get_page` has three required arguments:

    ``number``
        The page number to retrieve, as a 1-based index. The given value is validated in the following ways:

        * If it is not an integer, ``Paginator`` raises a ``PageNotAnInteger`` exception. ``get_page()`` catches this and returns the first page of results instead.
        * If it is less than ``1``, ``Paginator`` raises an ``EmptyPage`` exception. ``get_page()`` catches this and returns the first page of results instead.
        * If it is over the maximum number of pages for the given item sequence, ``Paginator`` also raises an ``EmptyPage`` exception. ``get_page()`` catches this and returns the last page of results instead.

    ``object_list``
        The sequence of items from which to retrieve the specified page. As per the ``Paginator`` object itself, the sequence can be a list, tuple, Django ``QuerySet``, or any other sliceable object with a ``count()`` or ``__len__()`` method.

    ``per_page``
        The number of results to be included in each page. While required by default, a project-wide default value can be set that removes the need to specify ``per_page`` on every call. See :ref:`pagination-page-length` below.

While ``get_page()`` only returns a ``Page`` instance, the ``Paginator`` that created it is accessible through the ``Page.paginator`` attribute. Adapting `Django's example <https://docs.djangoproject.com/en/stable/topics/pagination/#example>`_:

.. code-block:: python

    >>> from djem.pagination import get_page
    >>> objects = ['john', 'paul', 'george', 'ringo']
    >>> page1 = get_page(1, objects, per_page=2)

    >>> page1.paginator.count
    4
    >>> page1.paginator.num_pages
    2
    >>> page1.paginator.page_range
    range(1, 3)

    >>> page1
    <Page 1 of 2>
    >>> page1.object_list
    ['john', 'paul']
    >>> page1.has_next()
    True
    >>> page1.has_previous()
    False

    >>> get_page('spam', objects, per_page=2)
    <Page 1 of 2>

    >>> get_page(-1, objects, per_page=2)
    <Page 1 of 2>

    >>> get_page(9999, objects, per_page=2)
    <Page 2 of 2>

``get_page()`` also accepts all remaining keyword arguments of the ``Paginator`` constructor, which are passed through to the ``Paginator`` instance created internally. For example, using the ``orphans`` argument with the above example:

.. code-block:: python

    >>> get_page(1, objects, per_page=3)
    <Page 1 of 2>

    >>> get_page(1, objects, per_page=3, orphans=1)
    <Page 1 of 1>

``get_page()`` can still raise an ``EmptyPage`` exception if ``allow_empty_first_page=False`` is given and the ``object_list`` is empty:

.. code-block:: python

    >>> from djem.pagination import get_page
    >>> objects = []
    >>> page1 = get_page(1, objects, per_page=20, allow_empty_first_page=False)
    Traceback (most recent call last):
    ...
    EmptyPage: That page contains no results

.. note::

    :func:`get_page` differs from the ``Paginator.get_page()`` `method introduced in Django 2.0 <https://docs.djangoproject.com/en/2.0/topics/pagination/#django.core.paginator.Paginator.get_page>`_ in two ways:

    * The default page length support :ref:`described below <pagination-page-length>`.
    * The behaviour of an out-of-range page number: For numbers less than 1, ``Paginator.get_page()`` returns the *last page* while ``get_page()`` returns the *first* page.

.. _pagination-page-length:

Controlling page length
-----------------------

In a lot of cases, sites use a standard page length for multiple (sometimes numerous) paginated lists they display. Djem reduces the need to specify this value in repeated calls to :func:`get_page` by providing a setting that defines this standard page length: :ref:`setting-DJEM_DEFAULT_PAGE_LENGTH`.

If added to your ``settings.py`` file, ``get_page()`` will use the defined page length in any call that does not explicitly pass the ``per_page`` argument. Providing the argument will override the default on a call-by-call basis.

Not providing the ``per_page`` argument when ``DJEM_DEFAULT_PAGE_LENGTH`` is **not** defined in ``settings.py`` will result in an exception.


In the template
===============

Rendering a block of links to control pagination of a result list (first, last, next, previous, etc) can also involve boilerplate code and repetition. The :ref:`tags-paginate` template tag allows one-line generation of such pagination links. Simply pass it the same Django ``Page`` instance used to render the list itself and it will render appropriate page navigation links. This allows quick and easy rendering of a consistent paged-list navigation block site wide.

For example, where ``user_list`` is a ``Page`` instance:

.. code-block:: html+django

    {% load djem %}
    ...
    {% for user in user_list %}
        {{ user.name }}
    {% endfor %}
    {% paginate user_list %}
    ...

The structure of the navigation block that is rendered is controlled by the ``djem/pagination.html`` template. Djem ships with a default template, but (as per any template provided by a Django app) this can be overridden by a specific project. See the `Django documentation for overriding templates <https://docs.djangoproject.com/en/stable/howto/overriding-templates/>`_.

By default, the block will be rendered as a HTML ordered list (``<ol>``) with the following items:

* A link to the first page, labelled "First" (hidden if displaying the first page)
* A link to the previous page, labelled "Previous" (hidden if displaying the first page)
* "Page X of Y", where X is the current page number and Y is the total number of pages
* A link to the next page, labelled "Next" (hidden if displaying the last page)
* A link to the last page, labelled "Last" (hidden if displaying the last page)

The links are defined simply as "?page=n", where n is the relevant page number.

To alter the labels, change the format of the links (e.g. the name of the ``GET`` param), or completely change which links are displayed (e.g. adding links to individual page numbers), the ``djem/pagination.html`` will need to be overridden. However, this is not necessary to simply style the default navigation block. The following CSS classes are available.

* The ``<ol>`` element has the ``pagination`` class
* The ``<li>`` element containing the first page link has the ``pagination__first`` class
* The ``<li>`` element containing the previous page link has the ``pagination__previous`` class
* The ``<li>`` element containing the next page link has the ``pagination__next`` class
* The ``<li>`` element containing the last page link has the ``pagination__last`` class
