from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.template import engines

from djem.ajax import AjaxResponse

from .models import CommonInfoTest


# --- AjaxResponse test views --> #

def ajax__no_args(request):
    
    return AjaxResponse()


def ajax__request_only(request):
    
    return AjaxResponse(request)


def ajax__data(request):
    
    return AjaxResponse(request, {'test': 'test'})


def ajax__bad_data(request):
    
    return AjaxResponse(request, ['test1', 'test2'])


def ajax__success__true(request):
    
    return AjaxResponse(request, success=True)


def ajax__success__false(request):
    
    return AjaxResponse(request, success=False)


def ajax__success__dumb(request):
    
    return AjaxResponse(request, success='dumb')


def ajax__success__data(request):
    
    return AjaxResponse(request, {'test': 'test'}, success=True)


def ajax__messages_(request):
    
    messages.success(request, 'This is a success message.')
    messages.error(request, 'This is an error message.')
    messages.add_message(request, messages.INFO, 'This is an info message.', extra_tags='special')
    
    return AjaxResponse(request)


def ajax__messages__data(request):
    
    messages.success(request, 'This is a success message.')
    
    return AjaxResponse(request, {'test': 'test'})

# <-- AjaxResponse test views --- #


# --- csrfify_ajax template tag test views --> #

def csrfify_ajax__valid__explicit(request):
    
    template = engines['django'].from_string(
        "{% load djem %}\n{% csrfify_ajax 'jquery' %}"
    )
    
    return HttpResponse(template.render({}, request))


def csrfify_ajax__valid__implicit(request):
    
    template = engines['django'].from_string(
        "{% load djem %}\n{% csrfify_ajax %}"
    )
    
    return HttpResponse(template.render({}, request))


def csrfify_ajax__invalid(request):
    
    template = engines['django'].from_string(
        "{% load djem %}\n{% csrfify_ajax 'invalid' %}"
    )
    
    return HttpResponse(template.render({}, request))

# <-- csrfify_ajax template tag test views --- #


# --- ifperm/ifnotperm template tag test views --> #

def ifperm__render(request):
    
    return render(request, 'app/ifperm_test.html', {
        'obj': CommonInfoTest.objects.first()
    })


def ifnotperm__render(request):
    
    return render(request, 'app/ifnotperm_test.html', {
        'obj': CommonInfoTest.objects.first()
    })

# <-- ifperm/ifnotperm template tag test views --- #
