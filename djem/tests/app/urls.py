from django.conf.urls import url

from .views import (  # isort:skip
    ajax__bad_data, ajax__data, ajax__messages_, ajax__messages__data,
    ajax__no_args, ajax__request_only, ajax__success__data,
    ajax__success__dumb, ajax__success__false, ajax__success__true
)

from .views import (  # isort:skip
    csrfify_ajax__valid__explicit, csrfify_ajax__valid__implicit,
    csrfify_ajax__invalid, ifnotperm__render, ifperm__render
)

from .views import (  # isort:skip
    redir_custom, redir_login,
    perm_decorator__string__add,
    perm_decorator__string__add__custom_redir,
    perm_decorator__string__add__raise,
    perm_decorator__string__delete,
    perm_decorator__string__invalid,
    perm_decorator__tuple,
    perm_decorator__tuple__custom_redir,
    perm_decorator__tuple__raise,
    perm_decorator__tuple__invalid,
    perm_decorator__multiple__add_delete,
    perm_decorator__multiple__view_delete,
    perm_decorator__multiple__view_delete__custom_redir,
    perm_decorator__multiple__view_delete__raise,
    perm_decorator__multiple__invalid
)

from .views import PermissionProtectedView  # isort:skip

urlpatterns = [
    url(r'^accounts/login/$', redir_login),  # for standard unauthenticated user redirects
    url(r'^custom/$', redir_custom),  # for custom unauthenticated user redirects
    
    # AjaxResponse test urls
    url(r'^test/ajax/no_args/$', ajax__no_args, name='ajax__no_args'),
    url(r'^test/ajax/request_only/$', ajax__request_only, name='ajax__request_only'),
    url(r'^test/ajax/data/$', ajax__data, name='ajax__data'),
    url(r'^test/ajax/bad_data/$', ajax__bad_data, name='ajax__bad_data'),
    url(r'^test/ajax/success__true/$', ajax__success__true, name='ajax__success__true'),
    url(r'^test/ajax/success__false/$', ajax__success__false, name='ajax__success__false'),
    url(r'^test/ajax/success__dumb/$', ajax__success__dumb, name='ajax__success__dumb'),
    url(r'^test/ajax/success__data/$', ajax__success__data, name='ajax__success__data'),
    url(r'^test/ajax/messages/$', ajax__messages_, name='ajax__messages'),
    url(r'^test/ajax/messages__data/$', ajax__messages__data, name='ajax__messages__data'),
    
    # csrfify_ajax template tag test urls
    url(r'^test/csrfify/valid/explicit/$', csrfify_ajax__valid__explicit, name='csrfify_ajax__valid__explicit'),
    url(r'^test/csrfify/valid/implicit/$', csrfify_ajax__valid__implicit, name='csrfify_ajax__valid__implicit'),
    url(r'^test/csrfify/invalid/$', csrfify_ajax__invalid, name='csrfify_ajax__invalid'),
    
    # ifperm/ifnotperm template tag test urls
    url(r'^test/ifperm/render/$', ifperm__render, name='ifperm__render'),
    url(r'^test/ifnotperm/render/$', ifnotperm__render, name='ifnotperm__render'),
    
    # permission_required decorator test urls
    url(
        r'^test/perm_decorator/string/add/(?P<pk>\d+)/$',
        perm_decorator__string__add,
        name='perm_decorator__string__add'
    ),
    url(
        r'^test/perm_decorator/string/add/(?P<pk>\d+)/custom_redir/$',
        perm_decorator__string__add__custom_redir,
        name='perm_decorator__string__add__custom_redir'
    ),
    url(
        r'^test/perm_decorator/string/add/(?P<pk>\d+)/raise/$',
        perm_decorator__string__add__raise,
        name='perm_decorator__string__add__raise'
    ),
    url(
        r'^test/perm_decorator/string/delete/(?P<pk>\d+)/$',
        perm_decorator__string__delete,
        name='perm_decorator__string__delete'
    ),
    url(
        r'^test/perm_decorator/string/invalid/(?P<pk>\d+)/$',
        perm_decorator__string__invalid,
        name='perm_decorator__string__invalid'
    ),
    url(
        r'^test/perm_decorator/tuple/(?P<pk>\d+)/$',
        perm_decorator__tuple,
        name='perm_decorator__tuple'
    ),
    url(
        r'^test/perm_decorator/tuple/(?P<pk>\d+)/custom_redir/$',
        perm_decorator__tuple__custom_redir,
        name='perm_decorator__tuple__custom_redir'
    ),
    url(
        r'^test/perm_decorator/tuple/(?P<pk>\d+)/raise/$',
        perm_decorator__tuple__raise,
        name='perm_decorator__tuple__raise'
    ),
    url(
        r'^test/perm_decorator/tuple/invalid/(?P<pk>\d+)/$',
        perm_decorator__tuple__invalid,
        name='perm_decorator__tuple__invalid'
    ),
    url(
        r'^test/perm_decorator/multiple/view_delete/(?P<pk>\d+)/$',
        perm_decorator__multiple__view_delete,
        name='perm_decorator__multiple__view_delete'
    ),
    url(
        r'^test/perm_decorator/multiple/view_delete/(?P<pk>\d+)/custom_redir/$',
        perm_decorator__multiple__view_delete__custom_redir,
        name='perm_decorator__multiple__view_delete__custom_redir'
    ),
    url(
        r'^test/perm_decorator/multiple/view_delete/(?P<pk>\d+)/raise/$',
        perm_decorator__multiple__view_delete__raise,
        name='perm_decorator__multiple__view_delete__raise'
    ),
    url(
        r'^test/perm_decorator/multiple/add_delete/(?P<pk>\d+)/$',
        perm_decorator__multiple__add_delete,
        name='perm_decorator__multiple__add_delete'
    ),
    url(
        r'^test/perm_decorator/multiple/invalid/(?P<pk>\d+)/$',
        perm_decorator__multiple__invalid,
        name='perm_decorator__multiple__invalid'
    ),
    
    # PermissionRequiredMixin decorator test urls
    url(
        r'^test/perm_mixin/unconfigured/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(),
        name='perm_mixin__unconfigured'
    ),
    url(
        r'^test/perm_mixin/string/add/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required='app.add_optest'),
        name='perm_mixin__string__add'
    ),
    url(
        r'^test/perm_mixin/string/delete/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required='app.delete_optest'),
        name='perm_mixin__string__delete'
    ),
    url(
        r'^test/perm_mixin/string/invalid/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required='fail'),
        name='perm_mixin__string__invalid'
    ),
    url(
        r'^test/perm_mixin/tuple/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required=(('app.delete_optest', 'pk'), )),
        name='perm_mixin__tuple'
    ),
    url(
        r'^test/perm_mixin/tuple/invalid/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required=(('fail', 'pk'), )),
        name='perm_mixin__tuple__invalid'
    ),
    url(
        r'^test/perm_mixin/multiple/view_delete/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required=('app.view_optest', ('app.delete_optest', 'pk'))),
        name='perm_mixin__multiple__view_delete'
    ),
    url(
        r'^test/perm_mixin/multiple/add_delete/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required=('app.add_optest', ('app.delete_optest', 'pk'))),
        name='perm_mixin__multiple__add_delete'
    ),
    url(
        r'^test/perm_mixin/multiple/invalid/(?P<pk>\d+)/$',
        PermissionProtectedView.as_view(permission_required=('app.view_optest', ('fail', 'pk'))),
        name='perm_mixin__multiple__invalid'
    ),
]
