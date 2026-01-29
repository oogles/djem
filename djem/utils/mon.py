import logging
import resource
import time

from django.db import connection

from djem.utils.table import Table


def _get_mem_mb():
    
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000


def _get_query_count():
    
    return len(connection.queries)


def _get_stat_table_data(monitor, stat):
    
    if stat not in {'time', 'queries', 'mem'}:
        msg = f'Unknown statistic "{stat}".'
        raise TypeError(msg)
    
    total_key = f'total_{stat}'
    min_key = f'min_{stat}'
    max_key = f'max_{stat}'
    avg_key = f'avg_{stat}'
    
    # Each statistic should be formatted slightly differently
    stat_format_map = {
        'time': '{0:.4f}',
        'queries': '{0}',
        'mem': '{0:.3f}'
    }
    
    stat_format = stat_format_map[stat]
    
    data = []
    
    def build_data(parent, _indent=0):
        
        indent_str = ' ' * _indent
        parent_total = parent.stats[total_key]
        
        # Sort the monitors by their total historical runtimes
        children = sorted(parent.children.values(), key=lambda m: m.stats[total_key], reverse=True)
        
        for child in children:
            total = child.stats[total_key]
            
            pc = 0
            if parent_total:
                pc = total / parent_total * 100
            
            data.append((
                f'{indent_str}{child.name}',
                stat_format.format(child.stats[min_key]),
                stat_format.format(child.stats[max_key]),
                stat_format.format(child.stats[avg_key]),
                stat_format.format(total),
                child.stats['count'],
                f'{indent_str}{pc:.2f}%',
            ))
            
            if child.children:
                build_data(child, _indent=_indent + 1)
    
    build_data(monitor)
    
    return data


def _get_stat_table(monitor, title, stats):
    
    # Include a separator between the output for each statistic, using a
    # combination of blank rows and a row to act as a title for the statistic
    include_separator = len(stats) > 1
    stat_heading_map = {
        'time': 'Timing',
        'queries': 'Queries',
        'mem': 'Memory'
    }
    
    footer = f'Totals: {monitor.get_total_string(include_name=False)}'
    
    t = Table(
        title=title,
        footer=footer
    )
    
    # Add headings manually, as standard row, to avoid doubling the HRs used
    # in the stat titles below
    t.add_row(['Name', 'Minimum', 'Maximum', 'Average', 'Total', 'Count', '%'])
    
    if not include_separator:
        t.add_row(Table.HR)
    
    for stat in stats:
        if include_separator:
            t.add_row(Table.HR)
            t.add_full_width_row(stat_heading_map[stat])
            t.add_row(Table.HR)
        
        t.add_rows(_get_stat_table_data(monitor, stat))
    
    return t.build_table()


class M:
    """
    An individual monitor instance, typically created and managed by :class:`Mon`.
    
    Tracks runtime, memory usage, and database query counts occurring between
    calls to :meth:`start` and :meth:`stop`.
    
    :param name: The name of the monitor.
    :param parent: An optional parent :class:`M` instance.
    """
    
    def __init__(self, name, parent=None):
        
        self.name = name
        
        self.parent = parent
        self.children = {}
        self.active_children = 0
        
        if parent:
            parent.children[name] = self
        
        self.stats = None
        
        self.start_time = None
        self.end_time = None
        self.start_mem = None
        self.end_mem = None
        self.start_queries = None
        self.end_queries = None
    
    def _update_stats(self):
        
        if not self.end_time:
            msg = 'Monitor not started or still running.'
            raise RuntimeError(msg)
        
        stats = self.stats
        runtime = self.get_runtime()
        mem_usage = self.get_mem_usage()
        query_count = self.get_query_count()
        
        if stats is None:
            self.stats = {
                'count': 1,
                
                'min_time': runtime,
                'max_time': runtime,
                'avg_time': runtime,
                'total_time': runtime,
                
                'min_mem': mem_usage,
                'max_mem': mem_usage,
                'avg_mem': mem_usage,
                'total_mem': mem_usage,
                
                'min_queries': query_count,
                'max_queries': query_count,
                'avg_queries': query_count,
                'total_queries': query_count
            }
            
            return
        
        stats['count'] += 1
        
        stats['total_time'] += runtime
        stats['total_mem'] += mem_usage
        stats['total_queries'] += query_count
        
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['avg_mem'] = stats['total_mem'] / stats['count']
        stats['avg_queries'] = stats['total_queries'] / stats['count']
        
        stats['min_time'] = min(stats['min_time'], runtime)
        stats['min_mem'] = min(stats['min_mem'], mem_usage)
        stats['min_queries'] = min(stats['min_queries'], query_count)
        
        stats['max_time'] = max(stats['max_time'], runtime)
        stats['max_mem'] = max(stats['max_mem'], mem_usage)
        stats['max_queries'] = max(stats['max_queries'], query_count)
    
    def start(self):
        """
        Start the monitor.
        """
        
        if self.parent:
            self.parent.active_children += 1
        
        self.start_time = time.time()
        self.start_queries = _get_query_count()
        self.start_mem = _get_mem_mb()
    
    def stop(self):
        """
        Stop the monitor.
        """
        
        self.end_time = time.time()
        self.end_mem = _get_mem_mb()
        self.end_queries = _get_query_count()
        self._update_stats()
        
        if self.parent:
            self.parent.active_children -= 1
        
        if self.active_children > 0:
            msg = 'Cannot end a monitor with running children.'
            raise RuntimeError(msg)
    
    def _get_stat(self, start_value, end_value, current_value_fn):
        
        if start_value is None:
            msg = 'Monitor not started.'
            raise RuntimeError(msg)
        
        if end_value is None:
            end_value = current_value_fn()
        
        return end_value - start_value
    
    def get_mem_usage(self):
        """
        Return the memory usage (in MB) between the start and end of the monitor.
        
        :return: Memory usage in MB.
        :raises RuntimeError: If the monitor has not been stopped.
        """
        
        return self._get_stat(self.start_mem, self.end_mem, _get_mem_mb)
    
    def get_query_count(self):
        """
        Return the number of database queries executed between the start and
        end of the monitor.
        
        :return: Number of database queries.
        :raises RuntimeError: If the monitor has not been stopped.
        """
        
        return self._get_stat(self.start_queries, self.end_queries, _get_query_count)
    
    def get_runtime(self):
        """
        Return the elapsed time in seconds between the start and end of the
        monitor.
        
        :return: Elapsed time in seconds.
        :raises RuntimeError: If the monitor has not been stopped.
        """
        
        return self._get_stat(self.start_time, self.end_time, time.time)
    
    def reset(self):
        """
        Reset the start and end values of tracked metrics to allow reuse of the
        monitor instance. Gathered statistics are preserved.
        """
        
        self.start_time = None
        self.end_time = None
        self.start_queries = None
        self.end_queries = None
        self.start_mem = None
        self.end_mem = None
    
    def get_total_string(self, include_name=True):
        """
        Return a summary string of the total runtime, query count, and memory
        usage of the monitor.
        
        :param include_name: Whether to include the monitor's name in the output.
        :return: The summary string.
        """
        
        seconds = self.get_runtime()
        queries = self.get_query_count()
        mem_usage = self.get_mem_usage()
        
        totals = f'{seconds:.4f} seconds, {queries} queries, {mem_usage:.3f}MB of RAM'
        
        if include_name:
            totals = f'{self.name}: {totals}'
        
        return totals
    
    def get_results(self, time=True, queries=False, mem=False):
        """
        Return formatted results for this monitor and its children.
        
        If the monitor has no children, output is equivalent to :meth:`get_total_string`.
        
        If the monitor has children, output is a formatted table showing
        statistics for each child, for each of the requested metrics. Children
        under each metric are sorted by the percentage of the parent's total
        that is represented by that child. By default, only timing statistics
        are included in the table.
        
        :param time: Whether to include timing statistics in the table.
        :param queries: Whether to include database query statistics in the table.
        :param mem: Whether to include memory usage statistics in the table.
        :return: The formatted results string.
        """
        
        if not self.children:
            return self.get_total_string()
        
        stats = []
        if time:
            stats.append('time')
        if queries:
            stats.append('queries')
        if mem:
            stats.append('mem')
        
        return _get_stat_table(self, 'Monitor Results', stats)
    
    def __str__(self):
        
        if not self.end_time:
            return f'{self.name}: Running'
        
        return self.get_total_string()


class Mon:
    """
    A management class for individual monitors (:class:`M` instances).
    
    Allows simple start/stop operations by name, and supports nesting monitors
    to provide more in-depth profiling of code sections. Any number of nested
    monitors are supported, they can be included in loops, etc. Parent monitors
    will accumulate statistics from their child monitors, including number of
    times called and min/max/avg values for time, queries, and memory usage.
    
    The :meth:`stop` method returns the stopped :class:`M` instance for the
    named monitor, allowing access to its statistics and results.
    
    Basic usage::
        
        from djem import Mon
        
        Mon.start('my_monitor')
        # ... code to monitor ...
        print(Mon.stop('my_monitor'))
    
    Nested usage::
        
        from djem import Mon
        
        Mon.start('outer_monitor')
        # ... code to monitor ...
        
        Mon.start('inner_monitor')
        # ... code to monitor ...
        Mon.stop('inner_monitor')
        
        print(Mon.stop('outer_monitor').get_results())
    """
    
    monitors = {}
    
    last_m = None
    
    @classmethod
    def start(cls, name):
        """
        Start a new monitor with the given ``name``. Another monitor with the
        same name cannot be active at the same time.
        
        If another monitor is already active, it will become the parent of the
        new monitor being started. The new monitor will become the parent of
        any subsequently started monitors, until it is stopped.
        
        :param name: The name of the monitor to start.
        :raises RuntimeError: If a monitor with the given name is already active.
        """
        
        if name in cls.monitors:
            msg = f'Cannot start a monitor which has not been ended ({name}).'
            raise RuntimeError(msg)
        
        # Re-use an existing monitor with the same name on the same parent, if
        # there is one (this allows the same monitor object to build up stats).
        try:
            m = cls.last_m.children[name]
        except (AttributeError, KeyError):
            m = M(name, cls.last_m)
        else:
            m.reset()  # for re-use
        
        cls.monitors[name] = m
        
        # Remember this monitor as the most recently started. It will become
        # the parent of the next monitor that is started.
        cls.last_m = m
        
        m.start()
    
    @classmethod
    def stop(cls, name):
        """
        Stop the monitor with the given ``name`` and return the :class:`M`
        instance.
        
        The stopped monitor's parent, if any, becomes the current parent for
        subsequently started monitors.
        
        :param name: The name of the monitor to stop.
        :return: The stopped :class:`M` instance.
        :raises RuntimeError: If no monitor with the given name is active.
        """
        
        try:
            m = cls.monitors[name]
        except KeyError as e:
            msg = 'Attempted to end a monitor that was never started.'
            raise RuntimeError(msg) from e
        
        m.stop()
        
        cls.last_m = m.parent
        del cls.monitors[name]
        
        return m
    
    @classmethod
    def start_qlog(cls):
        """
        Start logging database queries to the console.
        
        Configure the ``django.db.backends`` logger to output at DEBUG level.
        """
        
        logger = logging.getLogger('django.db.backends')
        handler = logging.StreamHandler()
        
        cls._qlogger_original_level = logger.level
        cls._qlogger_handler = handler
        
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    
    @classmethod
    def stop_qlog(cls):
        """
        Stop logging database queries to the console.
        
        Revert the ``django.db.backends`` logger to its original level.
        """
        
        logger = logging.getLogger('django.db.backends')
        
        logger.setLevel(cls._qlogger_original_level)
        logger.addHandler(cls._qlogger_handler)
    
    @classmethod
    def reset(cls):
        """
        Discard all active monitors.
        """
        
        cls.monitors.clear()
        cls.last_m = None


def mon(name, allow_recursion=False):
    """
    A decorator to monitor the execution of a function using :class:`Mon`.
    
    When the function is called, a monitor with the given ``name`` is started.
    The monitor is stopped after the function completes, and the results are
    printed to the console.
    
    If a monitor with the given ``name`` is already running (for example, due
    to recursion), a ``RuntimeError`` is raised, unless ``allow_recursion`` is
    set to ``True``. In that case, a unique name is generated for each
    recursive invocation by appending an incrementing integer suffix to the
    base ``name``.
    
    Usage::
        
        from djem import mon
        
        @mon('my_monitor')
        def my_function():
            # ... code to monitor ...
    
    Any usage of :class:`Mon` within the context of the decorated function will
    be nested within the monitor created by the decorator.
    
    :param name: The name of the monitor.
    :param allow_recursion: Whether to allow recursive invocations by
        generating unique monitor names.
    :raises RuntimeError: If a monitor with the given name is already running and
        ``allow_recursion`` is ``False``.
    """
    
    def decorator(fn):
        
        def wrapper(*args, **kwargs):
            
            n = name
            
            if allow_recursion:
                i = 1
                while n in Mon.monitors:
                    n = '_'.join((n, str(i)))
                    i += 1
            
            try:
                Mon.start(n)
            except RuntimeError as e:
                # Monitor is already running, likely due to recursion. Update
                # the exception to note use of the `allow_recursion` flag.
                msg = (
                    f'Cannot start a monitor which has not been ended ({n}).'
                    ' If this is due to recursion, use the `allow_recursion`'
                    ' flag of the decorator.'
                )
                raise RuntimeError(msg) from e
            
            result = fn(*args, **kwargs)
            m = Mon.stop(n)
            
            # Only print stats if there is not a parent monitor - this monitor's
            # stats will be reported in its output if there is
            if not m.parent:
                print(m.get_results(time=True, queries=True, mem=True))
            
            return result
        
        return wrapper
    
    return decorator
