from functools import wraps

from django.contrib.messages import get_messages
from django.http import HttpResponseForbidden, JsonResponse
from django.template.defaultfilters import conditional_escape


def ajax_login_required(view_fn):
    """
    Simple decorator that returns ``HttpResponseForbidden`` if the user is not
    authenticated, and executes the decorated function if they are. Designed
    for use by views accessed with AJAX requests, where redirecting to the
    login view is not useful.
    """
    
    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        
        return view_fn(request, *args, **kwargs)
    
    return wrapper


class AjaxResponse(JsonResponse):
    """
    Extension of Django's ``JsonResponse`` with the following additional features:
    
    The first positional argument should be a Django ``HttpRequest`` instance.
    
    The ``data`` argument is optional. It may be modified (see below) before
    being passed to the parent ``JsonResponse``. If provided, it must always be
    a ``dict`` instance - using the ``safe`` argument of ``JsonResponse`` to
    JSON-encode other types is not supported.
    
    The optional argument ``success`` can be set to add a "success" attribute
    to the ``data`` dictionary.
    
    A "messages" attribute is automatically added to the ``data`` dictionary if
    the Django message framework store contains any messages at the time of the
    response. The messages in the store will be added as a list of dictionaries
    with the keys "message" and "tags".
    
    With the exception of ``safe``, as noted above, it supports all arguments of
    ``JsonResponse``.
    """
    
    def __init__(self, request, data=None, success=None, **kwargs):
        
        if data is None:
            data = {}
        
        if not isinstance(data, dict):
            raise TypeError('Non-dict data types are not supported')
        
        if success is not None:
            data['success'] = bool(success)
        
        messages = get_messages(request)
        if messages:
            # "Serialise" messages. Escape the message string as it would be
            # if the messages were rendered by an auto-escaping Django template.
            data['messages'] = [{'message': conditional_escape(m.message), 'tags': m.tags} for m in messages]
        
        super().__init__(data, **kwargs)
