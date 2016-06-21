from django.conf.urls import url

from .views import (
    ajax__bad_data, ajax__data, ajax__messages_, ajax__messages__data,
    ajax__no_args, ajax__request_only, ajax__success__data,
    ajax__success__dumb, ajax__success__false, ajax__success__true,
    ifnotperm__render, ifperm__render
)

urlpatterns = [
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
    
    url(r'^test/ifperm/render/$', ifperm__render, name='ifperm__render'),
    url(r'^test/ifnotperm/render/$', ifnotperm__render, name='ifnotperm__render'),
]
