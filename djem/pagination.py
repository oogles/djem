from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


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
