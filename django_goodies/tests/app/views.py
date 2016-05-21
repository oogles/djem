from django.contrib import messages

from django_goodies import AjaxResponse


def no_args(request):
    
    return AjaxResponse()


def request_only(request):
    
    return AjaxResponse(request)


def data(request):
    
    return AjaxResponse(request, {'test': 'test'})


def bad_data(request):
    
    return AjaxResponse(request, ['test1', 'test2'])


def success__true(request):
    
    return AjaxResponse(request, success=True)


def success__false(request):
    
    return AjaxResponse(request, success=False)


def success__dumb(request):
    
    return AjaxResponse(request, success='dumb')


def success__data(request):
    
    return AjaxResponse(request, {'test': 'test'}, success=True)


def messages_(request):
    
    messages.success(request, 'This is a success message.')
    messages.error(request, 'This is an error message.')
    messages.add_message(request, messages.INFO, 'This is an info message.', extra_tags='special')
    
    return AjaxResponse(request)


def messages__data(request):
    
    messages.success(request, 'This is a success message.')
    
    return AjaxResponse(request, {'test': 'test'})
