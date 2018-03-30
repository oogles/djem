=====
Utils
=====

.. module:: djem

``UNDEFINED``
=============

The :const:`UNDEFINED` constant is designed for use in argument default values.

Sometimes it is necessary to know whether *any* value was passed into a function or not, including values traditionally used as argument defaults (such as ``None``, ``False``, etc). Any given value would have an explicit meaning, with some default behaviour only performed if *nothing* was passed in.

Take the following contrived example:

.. code-block:: python

    def make_thing(name, label=None):

        if not label:
            label = name

        ...

The ``make_thing`` function takes a required ``name`` argument and an optional ``label`` argument. The label defaults to the name unless overridden with something more meaningful/verbose. But what if the caller would like their thing to have *no label*? And what if ``None``, ``False`` or an empty string could all indicate that? The function needs to differentiate those values from *nothing* being provided.

This example could be rewritten using :const:`UNDEFINED` in place of ``None`` as the argument default, allowing the caller to explicitly pass ``None`` to indicate that the label should not be given a default value:

.. code-block:: python

    from djem import UNDEFINED

    def make_thing(name, label=UNDEFINED):

        if label is UNDEFINED:
            label = name

        ...

:const:`UNDEFINED` is "falsey", so can also be used in more generic conditional statements:

.. code-block:: python

    from djem import UNDEFINED

    value = UNDEFINED

    if value:
        print('truthy')
    else:
        print('falsey')

    # output: 'falsey'
