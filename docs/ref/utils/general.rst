=============
General Utils
=============

.. module:: djem

``UNDEFINED``
=============

.. py:data:: UNDEFINED

The ``UNDEFINED`` constant is a falsey value designed for use in argument default values, for situations in which *any* value given (including traditional argument default values such as ``None``) have an explicit meaning.

.. code-block:: python

    from djem import UNDEFINED

    def make_thing(name, label=UNDEFINED):

        # None, the empty string, or False could indicate "no label" and need
        # to be distinguished from no value being provided
        if label is UNDEFINED:
            label = name

        ...

It can also be used in more generic conditional statements:

.. code-block:: python

    from djem import UNDEFINED

    value = UNDEFINED

    if value:
        print('truthy')
    else:
        print('falsey')

    # output: 'falsey'
