import inspect as inspector
import pprint
import types

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Manager, Model, QuerySet
from django.db.models.fields import NOT_PROVIDED
from django.utils.encoding import force_text

from djem.utils.table import Table


def get_defined_by(obj, attr):
    """
    Return the class that defines the given attribute on the given object.
    It may be the object's own class, or one of its parents.
    """
    
    if inspector.isclass(obj):
        cls = obj
    else:
        cls = obj.__class__
    
    for parent in reversed(cls.mro()):
        if hasattr(parent, attr):
            return parent
    
    defined_by = cls
    
    return defined_by


def inspectf(func):
    """
    Inspect a function, returning useful info such as its signature and where it
    is defined.
    """
    
    arguments = []
    
    argspec = inspector.getargspec(func)
    args = argspec.args
    defaults = argspec.defaults
    
    # There may be more arguments than defaults. Define an offset that will go
    # negative in that case. Increment it during the loop over args and begin
    # retrieving default values once it reaches 0.
    if not defaults:  # account for defaults being None
        offset = 0 - len(args)
    else:
        offset = len(defaults) - len(args)
    
    for arg_string in args:
        if offset >= 0:
            arg_string = '{0}={1}'.format(arg_string, defaults[offset])
        
        arguments.append(arg_string)
        offset += 1
    
    signature = '{0}({1})'.format(func.__name__, ', '.join(arguments))
    
    defined = 'Defined on line {line} of {module} ({path})'.format(
        line=func.__code__.co_firstlineno,
        module=func.__module__,
        path=func.__code__.co_filename
    )
    
    return '\n\n'.join((signature, func.__doc__ if func.__doc__ else '[no doc string]', defined))


class InspectTable:
    
    def get_preamble(self):
        
        return None
    
    def get_data_row_count(self):
        
        return 0
    
    def get_empty_string(self):
        
        return 'No results.'
    
    def get_title(self):
        
        return None
    
    def get_description(self):
        
        return None
    
    def get_headings(self):
        
        return None
    
    def get_footer(self):
        
        return None
    
    def populate_data(self, table):
        
        raise NotImplementedError()
    
    def build(self):
        
        output = [
            ''  # start with a blank line
        ]
        
        preamble = self.get_preamble()
        if preamble:
            output.append(preamble)
            output.append('')
        
        if not self.get_data_row_count():
            output.append(self.get_empty_string())
        else:
            t = Table(
                title=self.get_title(),
                footer=self.get_footer()
            )
            
            description = self.get_description()
            if description:
                t.add_full_width_row(description, 'centre')
                t.add_row(Table.HR)
            
            # Add headings manually to put them beneath the description row/s
            headings = self.get_headings()
            if headings:
                t.add_row(headings)
            
            self.populate_data(t)
            
            output.append(t.build_table())
        
        output.append('')  # end with a blank line
        
        return '\n'.join(output)


class ObjectTable(InspectTable):
    
    def __init__(
            self,
            obj,
            ignore_methods=False,
            ignore_inherited=False,
            ignore_private=True,
            ignore_magic=True):
        
        super().__init__()
        
        self.obj = obj
        self.ignore_methods = ignore_methods
        self.ignore_inherited = ignore_inherited
        self.ignore_private = ignore_private
        self.ignore_magic = ignore_magic
        
        magic, methods, other = self._inspect_obj()
        num_inspected = 0
        data_groups = []
        
        if magic:
            num_inspected += len(magic)
            data_groups.append(magic)
        
        if methods:
            num_inspected += len(methods)
            data_groups.append(methods)
        
        if other:
            num_inspected += len(other)
            data_groups.append(other)
        
        self.num_inspected = num_inspected
        self.data_groups = data_groups
    
    def _get_inspect_value(self, v, obj, attr):
        """
        Return the given value in a format suitable for output in the table.
        """
        
        if inspector.isclass(obj):
            cls = obj
        else:
            cls = obj.__class__
        
        if isinstance(v, Manager):
            try:
                model_field = cls._meta.get_field(attr)
            except FieldDoesNotExist:
                v = 'Manager on {0} model'.format(cls.__name__)
            else:
                v = 'Referencing {0} {1} records'.format(
                    v.count(),
                    model_field.related_model.__name__
                )
        elif isinstance(v, types.MethodType):
            v = 'pp({0}.{1})'.format(cls.__name__, attr)
        else:
            v = force_text(v)
        
        return v
    
    def _inspect_obj(self):
        
        obj = self.obj
        cls = obj.__class__
        
        ignore_methods = self.ignore_methods
        ignore_inherited = self.ignore_inherited
        ignore_private = self.ignore_private
        ignore_magic = self.ignore_magic
        
        magic = []
        methods = []
        other = []
        
        for attr in sorted(dir(obj)):
            is_magic = attr.startswith('__') and attr.endswith('__')
            
            if is_magic and ignore_magic:
                continue
            elif attr.startswith('_') and not is_magic and ignore_private:
                continue
            
            defined_by = get_defined_by(obj, attr).__name__
            if defined_by != cls.__name__ and ignore_inherited:
                continue
            
            try:
                v = getattr(obj, attr)
            except Exception as e:
                v = 'Error accessing attribute: {0}'.format(e)
                t = 'unknown'
            else:
                t = type(v).__name__
            
            if isinstance(v, types.MethodType):
                if ignore_methods:
                    continue
                
                title = '{0}()'.format(attr)
                append_to = methods
            else:
                title = force_text(attr)
                append_to = other
            
            if is_magic:
                append_to = magic
            
            append_to.append((
                defined_by,
                title,
                t,
                self._get_inspect_value(v, obj, attr)
            ))
        
        return magic, methods, other
    
    def get_data_row_count(self):
        
        return self.num_inspected
    
    def get_title(self):
        
        return 'Inspecting {0} instance'.format(self.obj.__class__.__name__)
    
    def get_description(self):
        
        ignoring = []
        if self.ignore_methods:
            ignoring.append('Methods')
        if self.ignore_magic:
            ignoring.append('Magic Stuff')
        if self.ignore_private:
            ignoring.append('Private Stuff')
        if self.ignore_inherited:
            ignoring.append('Inherited Stuff')
        
        description = []
        if ignoring:
            description.append('Ignoring: {0}'.format(', '.join(ignoring)))
        else:
            description.append('Ignoring: Nothing')
        
        try:
            mro = self.obj.mro()
        except AttributeError:
            # An instance - get the mro of the class
            mro = self.obj.__class__.mro()
        
        description.append('MRO: {0}'.format(', '.join([c.__name__ for c in mro])))
        
        return '\n'.join(description)
    
    def get_footer(self):
        
        num_inspected = self.num_inspected
        
        return '{0} attribute{1} inspected'.format(
            num_inspected,
            's' if num_inspected != 1 else ''
        )
    
    def populate_data(self, table):
        
        if not self.num_inspected:
            table.add_full_row('No attributes to inspect.')
            return
        
        for i, group in enumerate(self.data_groups):
            if i:
                table.add_row(Table.HR)
            
            table.add_rows(group)


class ModelTable(InspectTable):
    
    FIELD_TYPE_REPLACEMENT_MAP = {
        'Field': '',
        'ForeignKey': 'FK',
        'ManyToMany': 'M2M',
        'OneToOne': 'O2O',
        'ManyToOne': 'M2O'
    }
    
    def __init__(self, model, *field_filters, **kwargs):
        
        super().__init__()
        
        self.model = model
        self.field_filters = [f.lower() for f in field_filters]
        self.concrete_only = kwargs.pop('concrete_only', True)
        
        hierarchy, pk_hierarchy = self._get_hierarchies()
        
        self.hierarchy = hierarchy
        self.pk_hierarchy = pk_hierarchy
        
        self._discover_fields()
        
        self.total_discovered_fields = sum([c['num_discovered_fields'] for c in hierarchy])
        self.total_discovered_fields += 1  # add the pk
        
        self.total_matching_fields = sum([len(c['matching_fields']) for c in hierarchy])
    
    def _get_hierarchies(self):
        
        hierarchy = []
        pk_hierarchy = []
        
        for cls in reversed(self.model.mro()):
            try:
                meta = cls._meta
            except AttributeError:
                # This parent class is not a Model
                pass
            else:
                model_name = cls.__name__
                
                if meta.abstract:
                    model_name += ' [Abstract]'
                else:
                    pk_hierarchy.append(meta.pk.name)
                
                hierarchy.append({
                    'display_name': model_name,
                    'class': cls,
                    'meta': meta
                })
        
        return hierarchy, pk_hierarchy
    
    def _check_field_match(self, field):
        
        field_name = field.name.lower()
        
        for f in self.field_filters:
            if f in field_name:
                return True
        
        return False
    
    def _get_field_flags(self, field):
        
        if not field.concrete:
            # Abstract fields do not have most of the attributes checked below,
            # nor do they apply, so return early.
            return ['Not Concrete']
        
        flags = []
        
        if field.unique:
            flags.append('Unique')
        
        if field.null and not field.blank:
            flags.append('Not blank')
        
        if not field.editable:
            flags.append('Not editable')
        
        return flags
    
    def _get_field_type(self, field):
        
        field_type = field.__class__.__name__
        
        for string, replacement in self.FIELD_TYPE_REPLACEMENT_MAP.items():
            field_type = field_type.replace(string, replacement)
        
        # Add the foreign model to the type display of relationship fields
        rel = field.related_model
        if rel:
            # If a string reference, grab the model portion (if given in
            # <app_label>.<model> format). If a model class, use its name.
            if isinstance(rel, str):
                rel = rel.split('.')[-1]
            else:
                rel = rel.__name__
            
            field_type = '{0} ({1})'.format(field_type, rel)
        
        if not field.concrete:
            # Stop here for non-concrete fields
            return field_type
        
        # Add the size to the type display of CharField, DecimalField, etc
        try:
            size = field.max_digits
        except AttributeError:
            size = field.max_length
        else:
            try:
                size = '{0}/{1}'.format(size, field.decimal_places)
            except AttributeError:
                pass
        
        if size:
            field_type = '{0} ({1})'.format(field_type, size)
        
        return field_type
    
    def _get_field_default(self, field):
        
        default_value = field.default
        
        if default_value is NOT_PROVIDED:
            default_value = ''
        elif callable(default_value):
            default_value = '{0}()'.format(default_value.__name__)
        
        return default_value
    
    def _get_field_sort_key(self, field):
        
        prefix = 0
        
        if not field.concrete:
            # E.g. Automatic reverse ForeignKey field
            prefix = 3
        elif field.many_to_many:
            prefix = 2
        elif field.is_relation:
            prefix = 1
        
        return '{0}{1}'.format(prefix, field.name)
    
    def _discover_fields(self):
        
        # Track fields considered valid
        valid_fields = set()
        
        for config in self.hierarchy:
            num_discovered_fields = 0
            matching_fields = []
            
            all_fields = config['meta'].get_fields(include_parents=False)
            
            for field in sorted(all_fields, key=self._get_field_sort_key):
                if getattr(field, 'primary_key', False):
                    # Exclude primary key fields. Some automatic fields do not
                    # have the primary_key attribute to check.
                    continue
                
                if self.concrete_only and not field.concrete:
                    # Exclude non-concrete fields unless they are explicitly
                    # specified to be included
                    continue
                
                if field.name in valid_fields:
                    # This field has been processed before. Though the field
                    # list will exclude fields from parent models, it only
                    # excludes those from *concrete* parents. Fields from
                    # abstract parents should also be excluded.
                    continue
                
                # Consider "valid" before filtering out
                valid_fields.add(field.name)
                
                # Count against total before filtering out
                num_discovered_fields += 1
                
                # Apply field filters, if any
                if self.field_filters and not self._check_field_match(field):
                    continue
                
                field_type = self._get_field_type(field)
                default_value = self._get_field_default(field)
                flags = self._get_field_flags(field)
                
                matching_fields.append((
                    field.name,
                    field_type,
                    field.null,
                    default_value,
                    ', '.join(flags)
                ))
            
            config['matching_fields'] = matching_fields
            config['num_discovered_fields'] = num_discovered_fields
    
    def _get_model_row(self, config):
        
        attrs = [
            config['class'].__name__
        ]
        
        if config['meta'].abstract:
            attrs.append('[Abstract]')
        
        num_discovered_fields = config['num_discovered_fields']
        num_matching_fields = len(config['matching_fields'])
        
        if num_matching_fields == num_discovered_fields:
            attrs.append('\tDiscovered Fields: {0}'.format(num_discovered_fields))
        else:
            attrs.append('\tMatching Fields: {0}/{1}'.format(num_matching_fields, num_discovered_fields))
        
        return ' '.join(attrs)
    
    def get_data_row_count(self):
        
        return self.total_matching_fields
    
    def get_empty_string(self):
        
        filters = self.field_filters
        if filters:
            return 'Given filters matched no results: {0}'.format(filters)
        
        return 'No fields to display'
    
    def get_preamble(self):
        
        m = self.model
        hierarchy = self.hierarchy
        pk_hierarchy = self.pk_hierarchy
        
        lines = [
            'Model: {0}'.format(m.__name__),
            '\nInherits From:',
            ' - {0}'.format(
                '\n - '.join([c['display_name'] for c in hierarchy[:-1]])
            ),
            '\nUnique Together: {0}'.format(
                m._meta.unique_together if m._meta.unique_together else 'None'
            ),
            'Default Ordering: {0}'.format(
                m._meta.ordering if m._meta.ordering else 'None'
            ),
            '\n\nPK: {0} {1}'.format(
                m._meta.pk.name,
                ' ({0})'.format(' -> '.join(pk_hierarchy)) if len(pk_hierarchy) > 1 else ''
            )
        ]
        
        return '\n'.join(lines)
    
    def get_title(self):
        
        title = 'Fields on {0}'.format(self.model.__name__)
        
        filters = self.field_filters
        if filters:
            title = '{0} (matching {1})'.format(
                title,
                ' || '.join([repr(s) for s in filters])
            )
        
        if self.concrete_only:
            title = '{0} [Concrete Only]'.format(title)
        
        return title
    
    def get_headings(self):
        
        return ('', '', 'Null?', 'Default', 'Flags')
    
    def get_footer(self):
        
        if self.field_filters:
            return 'Fields: {0} / {1}'.format(self.total_matching_fields, self.total_discovered_fields)
        
        return 'Fields: {0}'.format(self.total_discovered_fields)
    
    def populate_data(self, table):
        
        for config in self.hierarchy:
            matching_fields = config['matching_fields']
            if matching_fields:
                model_row = self._get_model_row(config)
                
                table.add_row(Table.HR)
                table.add_row(Table.BR)
                table.add_full_width_row(model_row)
                table.add_row(Table.BR)
                table.add_row(Table.HR)
                
                table.add_rows(matching_fields)


def pp(obj, *args, **kwargs):
    """
    Catch-all pretty-print/inspection function. Takes any object and tries to
    print the most useful representation of it. Additional args/kwargs depend
    on the type of object. Accepted types:
      - dictionaries, lists, tuples, sets and Django QuerySets: print using
        Python's pprint library. Accepts all args/kwargs of pprint.pprint().
      - functions/methods: print using inspectf. Accepts all args/kwargs of inspectf.
      - Django Model classes: print in a ModelTable. Accepts all constructor
        args/kwargs of ModelTable.
      - anything else: print in an ObjectTable. Accepts all constructor
        args/kwargs of ObjectTable.
    """
    
    # Force QuerySets to lists for pretty-printing
    if isinstance(obj, QuerySet):
        obj = list(obj)
    
    if isinstance(obj, (dict, list, tuple, set)):
        pprint.pprint(obj, *args, **kwargs)
        return
    
    function_types = (
        types.FunctionType,
        types.BuiltinFunctionType,
        types.MethodType,
        types.BuiltinMethodType
    )
    
    if isinstance(obj, function_types):
        print('\n', inspectf(obj, *args, **kwargs), '\n')
        return
    
    try:
        is_model_class = issubclass(obj, Model)
    except TypeError:
        # obj not a class
        pass
    else:
        if is_model_class:
            print(ModelTable(obj, *args, **kwargs).build())
            return
    
    print(ObjectTable(obj, *args, **kwargs).build())
