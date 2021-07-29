import datetime
import logging
import resource

from django.db import connection

from djem.utils.table import Table


def _get_mem_mb():
    
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000


def _get_query_count():
    
    return len(connection.queries)


def _get_stat_table_data(monitor, stat):
    
    if stat not in ('time', 'queries', 'mem'):
        raise TypeError('Unknown statistic "{0}".'.format(stat))
    
    total_key = 'total_{0}'.format(stat)
    min_key = 'min_{0}'.format(stat)
    max_key = 'max_{0}'.format(stat)
    avg_key = 'avg_{0}'.format(stat)
    
    # Each statistic should be formatted slightly differently
    stat_format_map = {
        'time': '{0:.4f}',
        'queries': '{0}',
        'mem': '{0:.3f}'
    }
    
    stat_format = stat_format_map[stat]
    
    data = []
    
    def build_data(parent, _indent=0):
        
        parent_total = parent.stats[total_key]
        
        # Sort the monitors by their total historical runtimes
        children = sorted(parent.children.values(), key=lambda m: m.stats[total_key], reverse=True)
        
        for child in children:
            total = child.stats[total_key]
            
            if parent_total:
                pc = total / parent_total * 100
            else:
                pc = 0
            
            data.append((
                '{0}{1}'.format(' ' * _indent, child.name),
                stat_format.format(child.stats[min_key]),
                stat_format.format(child.stats[max_key]),
                stat_format.format(child.stats[avg_key]),
                stat_format.format(total),
                child.stats['count'],
                '{0}{1:.2f}%'.format(' ' * _indent, pc),
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
    
    footer = 'Totals: {0}'.format(monitor.get_total_string(include_name=False))
    
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
            raise Exception('Monitor not started or still running.')
        
        stats = self.stats
        runtime = self.get_seconds()
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
        
        if runtime < stats['min_time']:
            stats['min_time'] = runtime
        
        if mem_usage < stats['min_mem']:
            stats['min_mem'] = mem_usage
        
        if query_count < stats['min_queries']:
            stats['min_queries'] = query_count
        
        if runtime > stats['max_time']:
            stats['max_time'] = runtime
        
        if mem_usage > stats['max_mem']:
            stats['max_mem'] = mem_usage
        
        if query_count > stats['max_queries']:
            stats['max_queries'] = query_count
    
    def start(self):
        
        if self.parent:
            self.parent.active_children += 1
        
        self.start_time = datetime.datetime.now()
        self.start_queries = _get_query_count()
        self.start_mem = _get_mem_mb()
    
    def stop(self):
        
        self.end_mem = _get_mem_mb()
        self.end_time = datetime.datetime.now()
        self.end_queries = _get_query_count()
        self._update_stats()
        
        if self.parent:
            self.parent.active_children -= 1
        
        if self.active_children > 0:
            raise Exception('Cannot end a monitor with running children.')
    
    def get_mem_usage(self):
        
        if self.start_mem is None:
            raise Exception('Monitor not started.')
        
        end_mem = self.end_mem
        if not end_mem:
            end_mem = _get_mem_mb()
        
        return end_mem - self.start_mem
    
    def get_query_count(self):
        
        if self.start_queries is None:
            raise Exception('Monitor not started.')
        
        end_queries = self.end_queries
        if not end_queries:
            end_queries = _get_query_count()
        
        return end_queries - self.start_queries
    
    def get_runtime(self):
        
        if self.start_time is None:
            raise Exception('Monitor not started.')
        
        end_time = self.end_time
        if not end_time:
            end_time = datetime.datetime.now()
        
        return end_time - self.start_time
    
    def get_seconds(self):
        
        return self.get_runtime().total_seconds()
    
    def reset(self):
        """
        Reset the start and end times to allow reuse.
        Do not clear statistics.
        """
        
        self.start_mem = None
        self.end_mem = None
        self.start_time = None
        self.end_time = None
    
    def get_total_string(self, include_name=True):
        
        totals = '{0:.4f} seconds, {1} queries, {2:.3f}MB of RAM'.format(
            self.get_seconds(),
            self.get_query_count(),
            self.get_mem_usage()
        )
        
        if include_name:
            totals = '{0}: {1}'.format(self.name, totals)
        
        return totals
    
    def print_mem_stats(self):
        
        if not self.children:
            print('{0}: {1:.3f}MB of RAM'.format(
                self.name,
                self.get_mem_usage()
            ))
            return
        
        print(_get_stat_table(self, 'Memory Usage Results', ('mem',)))
    
    def print_query_stats(self):
        
        if not self.children:
            print('{0}: {1} queries'.format(
                self.name,
                self.get_query_count()
            ))
            return
        
        print(_get_stat_table(self, 'Query Results', ('queries',)))
    
    def print_time_stats(self):
        
        if not self.children:
            print('{0}: {1:.4f} seconds'.format(
                self.name,
                self.get_seconds()
            ))
            return
        
        print(_get_stat_table(self, 'Timing Results', ('time',)))
    
    def print_stats(self):
        
        if not self.children:
            print(self.get_total_string())
            return
        
        print(_get_stat_table(self, 'Monitor Results', ('time', 'queries', 'mem')))
    
    def __str__(self):
        
        if not self.end_time:
            return '{0}: Running'.format(self.name)
        
        return self.get_total_string()


class Mon:
    
    monitors = {}
    
    last_m = None
    
    @classmethod
    def start(cls, name):
        
        if name in cls.monitors:
            print('Warning: Starting a monitor which has not been ended ({0})'.format(name))
        
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
        except KeyError:
            raise Exception('Attempted to end a monitor that was never started!')
        
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
            
            Mon.start(n)
            result = fn(*args, **kwargs)
            m = Mon.stop(n)
            
            # Only print stats if there is not a parent monitor - this monitor's
            # stats will be reported in its output if there is
            if not m.parent:
                m.print_stats()
            
            return result
        
        return wrapper
    
    return decorator
