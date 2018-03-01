from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def get_page(number, object_list, per_page=None, **kwargs):
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
        return paginator.page(number)
    except PageNotAnInteger:
        number = 1
    except EmptyPage:
        if number < 1:
            # Page number too low, return first page
            number = 1
        elif paginator.num_pages:
            # Page number too high, return last page
            number = paginator.num_pages
        else:
            # Paginator has no pages, still try for the first page. Will return
            # an empty page unless allow_empty_first_page is False.
            number = 1
    
    return paginator.page(number)
