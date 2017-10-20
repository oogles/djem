from django.template import Library, loader
from django.template.base import Node, NodeList, TemplateSyntaxError

register = Library()


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
    return t.render(context)


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
