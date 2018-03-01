from django.conf import settings
from django.template import Library, loader
from django.template.base import Node, NodeList, TemplateSyntaxError, token_kwargs

register = Library()

DEFAULT_FORM_FIELD_TAG = 'div'


#
# ifperm and ifnotperm are extremely similar to, and mostly copied directly
# from Django's ifequal and ifnotequal tags in django.template.defaulttags.
#

class IfPermNode(Node):
    
    child_nodelists = ('nodelist_true', 'nodelist_false')
    
    def __init__(self, user, perm, obj, nodelist_true, nodelist_false, negate):
        
        self.user = user
        self.perm = perm
        self.obj = obj
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.negate = negate
    
    def __repr__(self):
        
        if self.negate:
            return "<IfNotPermNode>"
        else:
            return "<IfPermNode>"
    
    def render(self, context):
        
        user = self.user.resolve(context, True)
        perm = self.perm.resolve(context, True)
        obj = self.obj.resolve(context, True)
        
        has_perm = user.has_perm(perm, obj)
        
        if (self.negate and not has_perm) or (not self.negate and has_perm):
            return self.nodelist_true.render(context)
        
        return self.nodelist_false.render(context)


def do_ifperm(parser, token, negate):
    
    bits = list(token.split_contents())
    if len(bits) != 4:
        raise TemplateSyntaxError("%r takes three arguments" % bits[0])
    
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    
    user = parser.compile_filter(bits[1])
    perm = parser.compile_filter(bits[2])
    obj = parser.compile_filter(bits[3])
    
    return IfPermNode(user, perm, obj, nodelist_true, nodelist_false, negate)


@register.tag
def ifperm(parser, token):
    """
    Outputs the contents of the block if the template context's user has the
    given permission on the given model object.
    
    Examples::
        {% ifperm 'blog.delete_blog' blog %}
            ...
        {% endifperm %}
        
        {% ifnotperm 'blog.change_blog' blog %}
            ...
        {% else %}
            ...
        {% endifnotperm %}
    """
    
    return do_ifperm(parser, token, False)


@register.tag
def ifnotperm(parser, token):
    """
    Outputs the contents of the block if the template context's user does not
    have the given permission on the given model object.
    See ifperm.
    """
    
    return do_ifperm(parser, token, True)


@register.simple_tag(takes_context=True)
def csrfify_ajax(context, lib='jquery'):
    """
    Add the X-CSRFToken header to all appropriate outgoing AJAX requests.
    Only usable in templates rendered using RequestContext.
    """
    
    t = loader.get_template('djem/csrfify_ajax/{0}.html'.format(lib))
    return t.render({
        'csrf_token': context['csrf_token']
    })


@register.inclusion_tag('djem/pagination.html')
def paginate(page):
    """
    Render a pagination block with appropriate links, based on the given Django
    Page object.
    """
    
    context = {
        'page': page
    }
    
    return context


def _transform_kwargs(kwargs):
    """
    Replace underscores in the given dictionary's keys with dashes. Used to
    convert keyword argument names (which cannot contain dashes) to HTML
    attribute names, e.g. data-*.
    """
    
    return {key.replace('_', '-'): kwargs[key] for key in kwargs.keys()}


@register.inclusion_tag('djem/form_field.html')
def form_field(field, extra_classes=None, **kwargs):
    """
    Render a form field, including the input, label, errorlist (if any), and
    help text block (if any), within a wrapping element.
    The wrapping element can be specified with ``DJEM_FORM_FIELD_TAG``. By
    default it is a div.
    It will have the CSS class "form-field", plus any classes defined by the
    field itself, plus any extra classes passed in to the tag as the second
    argument.
    Keyword arguments to the tag are added to the wrapping element as HTML
    attributes, with underscores (_) replaced with dashes (-) to allow
    attributes such as data-*.
    """
    
    # Convert underscores in keyword arguments to dashes, to support attributes
    # such as data-*, and since dashes are not valid in Python keyword argument
    # names
    kwargs = _transform_kwargs(kwargs)
    
    context = {
        'wrapper_tag': getattr(settings, 'DJEM_FORM_FIELD_TAG', DEFAULT_FORM_FIELD_TAG),
        'field': field,
        'extra_classes': extra_classes,
        'kwargs': kwargs
    }
    
    return context


class CheckboxNode(Node):
    
    child_nodelists = ('nodelist',)
    
    def __init__(self, field, nodelist, extra_classes, kwargs):
        
        self.field = field
        self.nodelist = nodelist
        self.extra_classes = extra_classes
        self.kwargs = kwargs
    
    def render(self, context):
        
        field = self.field.resolve(context)
        label = self.nodelist.render(context)
        
        if not label.strip():
            label = field.label
        
        extra_classes = self.extra_classes
        if extra_classes:
            extra_classes = self.extra_classes.resolve(context)
        
        kwargs = self.kwargs
        if kwargs:
            for k, v in self.kwargs.items():
                kwargs[k] = v.resolve(context)
            
            # Convert underscores in keyword arguments to dashes, to support
            # attributes such as data-*, and since dashes are not valid in
            # Python keyword argument names
            kwargs = _transform_kwargs(kwargs)
        
        return loader.render_to_string('djem/form_field.html', {
            'wrapper_tag': getattr(settings, 'DJEM_FORM_FIELD_TAG', DEFAULT_FORM_FIELD_TAG),
            'field': field,
            'extra_classes': extra_classes,
            'kwargs': kwargs,
            'checkbox_label': label
        })


@register.tag
def checkbox(parser, token):
    """
    Render a checkbox form field, including the input, label, errorlist (if any),
    and help text block (if any), within a wrapping element.
    Arguments and options as per the ``form_field`` tag.
    Unlike ``form_field``, this is a block tag whose content becomes the label
    for the checkbox, replacing the label specified by the field. This label is
    displayed *after* the checkbox input, as opposed to before.
    This tag allows the specification of labels that would otherwise not be
    possible, e.g. including links.
    E.g.
        {% checkbox form.terms_checkbox %}
            I agree to the <a href="{% url 'terms' %}" target="_blank">Terms of service</a>
        {% endcheckbox %}
    """
    
    bits = list(token.split_contents())
    if len(bits) < 2:
        raise TemplateSyntaxError('{0!r} takes at least one argument'.format(bits[0]))
    
    nodelist = parser.parse(('endcheckbox',))
    parser.next_token()  # consume {{ endcheckbox }}
    
    field = parser.compile_filter(bits[1])
    
    try:
        extra_classes = bits[2]
    except IndexError:
        extra_classes = None
        kwargs = None
    else:
        if '=' in extra_classes:
            extra_classes = None
            kwargs = bits[2:]
        else:
            extra_classes = parser.compile_filter(extra_classes)
            kwargs = bits[3:]
        
        kwargs = token_kwargs(kwargs, parser)
    
    return CheckboxNode(field, nodelist, extra_classes, kwargs)
