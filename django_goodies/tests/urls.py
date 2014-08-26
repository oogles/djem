from django.conf.urls import patterns, url

from .views import author_list, author_details, author_books, book_details

urlpatterns = patterns('',
    url(r'^django_goodies/test/author_list/$', author_list),
    (r'^django_goodies/test/author_details/$', author_details),
    (r'^django_goodies/test/author_books/$', author_books),
    (r'^django_goodies/test/book_details/$', book_details),
)
