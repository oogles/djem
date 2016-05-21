from django.conf.urls import url

from .views import (
    bad_data, data, messages_, messages__data, no_args, request_only,
    success__data, success__dumb, success__false, success__true
)

urlpatterns = [
    url(r'^test/no_args/$', no_args, name='no_args'),
    url(r'^test/request_only/$', request_only, name='request_only'),
    url(r'^test/data/$', data, name='data'),
    url(r'^test/bad_data/$', bad_data, name='bad_data'),
    url(r'^test/success__true/$', success__true, name='success__true'),
    url(r'^test/success__false/$', success__false, name='success__false'),
    url(r'^test/success__dumb/$', success__dumb, name='success__dumb'),
    url(r'^test/success__data/$', success__data, name='success__data'),
    url(r'^test/messages/$', messages_, name='messages'),
    url(r'^test/messages__data/$', messages__data, name='messages__data'),
]
