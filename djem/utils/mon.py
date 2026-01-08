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
        
        if self.parent:
            self.parent.active_children += 1
        
        self.start_time = time.time()
        self.start_queries = _get_query_count()
        self.start_mem = _get_mem_mb()
    
    def stop(self):
        
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
        
        return self._get_stat(self.start_mem, self.end_mem, _get_mem_mb)
    
    def get_query_count(self):
        
        return self._get_stat(self.start_queries, self.end_queries, _get_query_count)
    
    def get_runtime(self):
        
        return self._get_stat(self.start_time, self.end_time, time.time)
    
    def reset(self):
        """
        Reset the start and end times to allow reuse.
        Do not clear statistics.
        """
        
        self.start_time = None
        self.end_time = None
        self.start_queries = None
        self.end_queries = None
        self.start_mem = None
        self.end_mem = None
    
    def get_total_string(self, include_name=True):
        
        seconds = self.get_runtime()
        queries = self.get_query_count()
        mem_usage = self.get_mem_usage()
        
        totals = f'{seconds:.4f} seconds, {queries} queries, {mem_usage:.3f}MB of RAM'
        
        if include_name:
            totals = f'{self.name}: {totals}'
        
        return totals
    
    def get_results(self, time=True, queries=False, mem=False):
        
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
    
    monitors = {}
    
    last_m = None
    
    @classmethod
    def start(cls, name):
        
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
        
        logger = logging.getLogger('django.db.backends')
        handler = logging.StreamHandler()
        
        cls._qlogger_original_level = logger.level
        cls._qlogger_handler = handler
        
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    
    @classmethod
    def stop_qlog(cls):
        
        logger = logging.getLogger('django.db.backends')
        
        logger.setLevel(cls._qlogger_original_level)
        logger.addHandler(cls._qlogger_handler)
    
    @classmethod
    def reset(cls):
        
        cls.monitors.clear()
        cls.last_m = None


def mon(name, allow_recursion=False):
    
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
