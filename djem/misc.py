from django.conf import settings
from django.contrib.messages import get_messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.template.defaultfilters import escape


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
            data['messages'] = [{'message': escape(m.message), 'tags': m.tags} for m in messages]
        
        super(AjaxResponse, self).__init__(data, **kwargs)


def get_page(page, object_list, per_page=None, **kwargs):
    """
    Return the specified page, as a Django Page instance, from a Paginator
    constructed from the given object list and other keyword arguments.
    Handle InvalidPage exceptions and return logical valid pages instead.
    The ``per_page`` argument defaults to DJEM_DEFAULT_PAGE_LENGTH, if set.
    Otherwise, it is a required argument.
    """
    
    if per_page is None:
        try:
            per_page = settings.DJEM_DEFAULT_PAGE_LENGTH
        except AttributeError:
            raise TypeError('The "per_page" argument is required unless DJEM_DEFAULT_PAGE_LENGTH is set.')
    
    paginator = Paginator(object_list, per_page, **kwargs)
    
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        if page <= 0:
            objects = paginator.page(1)
        else:
            objects = paginator.page(paginator.num_pages)
    
    return objects
