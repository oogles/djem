from django.http import HttpResponse
from django.shortcuts import render
from django.template import engines

from .models import CommonInfoTest


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
