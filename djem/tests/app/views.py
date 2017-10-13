from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.template import engines
from django.views import View

from djem.ajax import AjaxResponse
from djem.auth import PermissionRequiredMixin, permission_required

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


# --- permission_required decorator test views --> #

# Target for standard unauthenticated user redirects
def redir_login(request):
    
    return HttpResponse('login')


# Target for custom unauthenticated user redirects
def redir_custom(request):
    
    return HttpResponse('custom')


@permission_required('app.add_optest')
def perm_decorator__string__add(request, pk):
    
    return HttpResponse('success')


@permission_required('app.add_optest', login_url='/custom/')
def perm_decorator__string__add__custom_redir(request, pk):
    
    return HttpResponse('success')


@permission_required('app.add_optest', raise_exception=True)
def perm_decorator__string__add__raise(request, pk):
    
    return HttpResponse('success')


@permission_required('app.delete_optest')
def perm_decorator__string__delete(request, pk):
    
    return HttpResponse('success')


@permission_required('fail')
def perm_decorator__string__invalid(request, pk):
    
    return HttpResponse('success')


@permission_required(('app.delete_optest', 'pk'))
def perm_decorator__tuple(request, pk):
    
    return HttpResponse('success')


@permission_required(('app.delete_optest', 'pk'), login_url='/custom/')
def perm_decorator__tuple__custom_redir(request, pk):
    
    return HttpResponse('success')


@permission_required(('app.delete_optest', 'pk'), raise_exception=True)
def perm_decorator__tuple__raise(request, pk):
    
    return HttpResponse('success')


@permission_required(('fail', 'pk'))
def perm_decorator__tuple__invalid(request, pk):
    
    return HttpResponse('success')


@permission_required('app.view_optest', ('app.delete_optest', 'pk'))
def perm_decorator__multiple__view_delete(request, pk):
    
    return HttpResponse('success')


@permission_required('app.view_optest', ('app.delete_optest', 'pk'), login_url='/custom/')
def perm_decorator__multiple__view_delete__custom_redir(request, pk):
    
    return HttpResponse('success')


@permission_required('app.view_optest', ('app.delete_optest', 'pk'), raise_exception=True)
def perm_decorator__multiple__view_delete__raise(request, pk):
    
    return HttpResponse('success')


@permission_required('app.add_optest', ('app.delete_optest', 'pk'))
def perm_decorator__multiple__add_delete(request, pk):
    
    return HttpResponse('success')


@permission_required('app.view_optest', ('fail', 'pk'))
def perm_decorator__multiple__invalid(request, pk):
    
    return HttpResponse('success')

# <-- permission_required decorator test views --- #


# --- PermissionRequiredMixin test views --> #

# urls configure the permission_required attribute
class PermissionProtectedView(PermissionRequiredMixin, View):
    
    def get(self, *args, **kwargs):
        
        return HttpResponse('success')

# <-- PermissionRequiredMixin test views --- #
