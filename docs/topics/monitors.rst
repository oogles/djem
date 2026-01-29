========
Monitors
========

.. currentmodule:: djem.utils.mon

Djem provides a simple monitoring system for tracking runtime, and database query counts (subject to the :ref:`caveats noted below <monitors-caveats>`), and memory usage during code execution. This is useful for profiling and optimising performance-critical code paths.

The monitoring system consists of three main components:

* :class:`M` - A monitor class that tracks statistics for a single code section. This rarely needs to be used directly.
* :class:`Mon` - A manager class for :class:`M` instances that handles monitor lifecycle and nesting.
* :func:`mon` - A decorator for automatically monitoring individual functions.

Monitors can be nested to provide hierarchical profiling of complex operations, providing additional statistics such as:

* Total number of times the same monitor is activated (e.g. if it exists within a loop).
* Min, max, and average for all three metrics (time, queries, memory) if the monitor is activated multiple times.
* Percentage of parent monitor's total value used by each child monitor.

Typical usage is via the :class:`Mon` management class, with the :func:`mon` decorator available as a shortcut when monitoring discrete functions. Both perform nesting automatically when a monitor is started while another is already active.


.. _monitors-caveats:

Caveats
=======

Use of the monitoring system has several caveats to be aware of:

* Monitors are not free. They do add some overhead, so code will run slower with monitors in place than it will without. This is especially pronounced when using monitors in large loops. So for statistics like total time taken, the absolute value is often less important than the percentage of a parent's total that a child uses. This still allows easy identification of bottlenecks within a process.
* There is a limitation on the number of queries that can be counted, as Django caps their query log to the most recent ``9000``. Once that log is full, monitors will stop noticing new queries. That will obviously affect the total query count included in the output, but it will also throw off other statistics such as averages. Nevertheless, by the time that number of queries has been executed, the major contributors to that query count should have been identified and the results will still highlight the offenders. If the number of queries exceeds ``9000``, you'll see the following warning, indicating the results for query counts may not be entirely accurate::
    
    UserWarning: Limit for query logging exceeded, only the last 9000 queries will be returned.

* The query log noted above is only populated when Django's debug mode is enabled (i.e. the ``DEBUG`` setting is ``True``). Therefore, query counts can only be monitored in debug mode. Timing and memory usage monitors will work regardless of the ``DEBUG`` setting.


Using the decorator
===================

The simplest way to use the monitoring system is with the :func:`mon` decorator:

.. code-block:: python
    
    from djem import mon
    
    @mon('fetch_users')
    def fetch_users():
        
        return User.objects.all()
    
    users = fetch_users()

This will transparently start and stop a monitor named ``fetch_users`` when the ``fetch_users()`` function is called. After the function completes, the monitor's results will be printed to the console.

Handling recursion
------------------

By default, the :func:`mon` decorator raises an error if a monitored function is called recursively:

.. code-block:: python

    @mon('recursive_process')
    def process_tree(node):
        
        result = process_node(node)
        
        for child in node.children:
            process_tree(child)  # RuntimeError!
        
        return result

To allow recursion, use the ``allow_recursion`` parameter:

.. code-block:: python

    @mon('recursive_process', allow_recursion=True)
    def process_tree(node):
        
        result = process_node(node)
        
        for child in node.children:
            process_tree(child)  # OK
        
        return result

Results will show suffixed monitor names for each recursive invocation (e.g. ``recursive_process``, ``recursive_process_1``, ``recursive_process_2``, etc.) nested within each other. Note that excessive amounts of recursion will make the results difficult to read.

Nesting
-------

Any use of :class:`Mon` (see :ref:`monitors-mon` below) within the context of the decorated function will be nested within the monitor created by the decorator. So this is valid:

.. code-block:: python
    
    from djem import Mon, mon
    
    @mon('complex_operation')
    def complex_operation():
        
        Mon.start('part_one')
        # ... code for part one ...
        Mon.stop('part_one')
        
        Mon.start('part_two')
        # ... code for part two ...
        Mon.stop('part_two')
    
    complex_operation()


.. _monitors-mon:

Using ``Mon``
=============

For more targeted monitoring, you can use the :class:`Mon` class directly:

.. code-block:: python

    from djem import Mon

    Mon.start('some_process')
    
    # ... code to monitor ...
    
    print(Mon.stop('some_process'))

Nesting
-------

Nesting monitors allows profiling different parts of a complex operation. Only the outermost monitor needs to output its results:

.. code-block:: python

    from djem import Mon
    
    Mon.start('complex_operation')
    
    # Monitor part one
    Mon.start('fetch_data')
    # ... code to fetch data ...
    Mon.stop('fetch_data')
    
    # Monitor part two
    Mon.start('transform_data')
    # ... code to transform data ...
    Mon.stop('transform_data')
    
    # Monitor part three
    Mon.start('save_results')
    # ... code to save results ...
    Mon.stop('save_results')
    
    m = Mon.stop('complex_operation')
    print(m.get_results(queries=True))

By default, only timing statistics are included when calling :meth:`~M.get_results`. In the above example, query counts are also included, via the ``queries=True`` flag. A ``mem=True`` flag is also available to include memory usage statistics.


Query Logging
=============

:class:`Mon` can also be used to enable console logging of executed database queries, via the ``django.db.backends`` logger. This is useful for debugging inefficient query usage.

.. code-block:: python

    from djem import Mon

    Mon.start_qlog()
    
    users = User.objects.filter(is_active=True)
    
    Mon.stop_qlog()
