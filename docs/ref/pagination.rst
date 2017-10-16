==========
Pagination
==========

.. module:: djem.pagination

``get_page``
============

.. function:: get_page(number, object_list, per_page=None, **kwargs)

    .. versionadded:: 0.5

    A simple wrapper around a Django ``Paginator`` that immediately invokes its ``page()`` method and returns a ``Page`` object.

    ``number`` is the number of the page to retrieve, as a 1-based index. If the given value is not an integer, or it is less than ``1``, it is treated as ``1``. If it is greater than the total number of pages, it is treated as ``Paginator.num_pages``.

    ``object_list`` is the sequence of items from which to retrieve the specified page - as a list, tuple, ``QuerySet`` or any other sliceable object with a ``count()`` or ``__len__()`` method.

    ``per_page`` is the number of results to be included in each page. Not required if :ref:`setting-DJEM_DEFAULT_PAGE_LENGTH` has been defined.

    All other keyword arguments of the ``Paginator`` constructor are also accepted and passed through to the ``Paginator`` instance created internally.
