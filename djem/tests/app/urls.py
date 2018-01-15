from django.conf.urls import url

from .views import (  # isort:skip
    csrfify_ajax__valid__explicit, csrfify_ajax__valid__implicit,
    csrfify_ajax__invalid, ifnotperm__render, ifperm__render
)

urlpatterns = [
    # csrfify_ajax template tag test urls
    url(r'^test/csrfify/valid/explicit/$', csrfify_ajax__valid__explicit, name='csrfify_ajax__valid__explicit'),
    url(r'^test/csrfify/valid/implicit/$', csrfify_ajax__valid__implicit, name='csrfify_ajax__valid__implicit'),
    url(r'^test/csrfify/invalid/$', csrfify_ajax__invalid, name='csrfify_ajax__invalid'),
    
    # ifperm/ifnotperm template tag test urls
    url(r'^test/ifperm/render/$', ifperm__render, name='ifperm__render'),
    url(r'^test/ifnotperm/render/$', ifnotperm__render, name='ifnotperm__render'),
]
