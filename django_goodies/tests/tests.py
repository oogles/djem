from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from ..utils.tests import RequestFactoryTestCase
from ..decorators import verify

from .models import Author, Book

@override_settings(ROOT_URLCONF='django_goodies.tests.urls')
class VerifyDecoratorTestCase(RequestFactoryTestCase):
    """
    Tests the behaviour of the `verify` decorator.
    """
    
    create_user = False
    
    def setUp(self):
        
        # Instances used by the tests
        self.author = Author.objects.create(name='John Smith')
        self.book = Book.objects.create(title='This Book Has No Title', author=self.author)
    
    #def test_invalid_view_args(self):
    #    """
    #    Test the decorated view being called with invalid arguments. The
    #    decorator should not interfere with the standard "blah blah blah"
    #    error in such cases.
    #    """
    #    
    #    pass
    
    ## --- Misconfigurations -->
    
    def test_invalid_base_redirect(self):
        """
        Test an invalid base redirect. It should raise a NoReverseMatch
        exception.
        """
        
        from django.core.urlresolvers import NoReverseMatch
        
        request = self.get_request('/django_goodies/test/author_list/')
        
        @verify('fail', (Author, 'author'))
        def view(request, author):
            raise Exception('Shouldn\'t be here')
        
        self.assertRaises(NoReverseMatch, view, request, author=None)
    
    def test_compact_config_invalid_arg_name(self):
        """
        Test an invalid argument name provided in a single compact verifier
        configuration. The argument should be considered optional and not be
        replaced with a model instance.
        """
        
        valid_author = self.author
        request = self.get_request('/django_goodies/test/author_list/')
        
        @verify('django_goodies.tests.views.author_details', (Author, 'fail'))
        def view(request, author):
            self.assertEqual(author, valid_author.pk)
        
        response = view(request, author=valid_author.pk)
    
    def test_full_config_invalid_arg_name(self):
        """
        Test an invalid argument name provided in a single full verifier
        configuration. The argument should be considered optional and not be
        replaced with a model instance.
        """
        
        valid_author = self.author
        request = self.get_request('/django_goodies/test/author_list/')
        
        @verify('django_goodies.tests.views.author_details', {
            'model': Author,
            'arg_name': 'fail'
        })
        def view(request, author):
            self.assertEqual(author, valid_author.pk)
        
        response = view(request, author=valid_author.pk)
    
    ## <-- Misconfigurations ---
    
    ## --- Single basic "model exists" check -->
    
    def test_valid_single_exists_compact(self):
        """
        Test a single "model exists" check on a valid model id, using the
        compact config. It should correctly replace the `author` argument of
        the view.
        """
        
        valid_author = self.author
        request = self.get_request('/django_goodies/test/author_list/')
        
        @verify('django_goodies.tests.views.author_details', (Author, 'author'))
        def view(request, author):
            self.assertEqual(author, valid_author)
        
        response = view(request, author=valid_author.pk)
    
    def test_invalid_single_exists_compact(self):
        """
        Test a single "model exists" check on an invalid model id, using the
        compact config. It should correctly redirect to the given fallback view.
        """
        
        invalid_id = 0
        redirect_view = 'django_goodies.tests.views.author_list'
        redirect_url = reverse(redirect_view)
        request = self.get_request('/django_goodies/test/author_details/')
        
        @verify(redirect_view, (Author, 'author'))
        def view(request, author):
            raise Exception('Shouldn\'t be here')
        
        response = view(request, author=invalid_id)
        self.assertRedirects(response, redirect_url)
    
    def test_valid_single_exists_full(self):
        """
        Test a single "model exists" check on a valid model id, using the
        full config. It should correctly replace the `author` argument of
        the view.
        """
        
        valid_author = self.author
        request = self.get_request('/django_goodies/test/author_list/')
        
        @verify('django_goodies.tests.views.author_details', {
            'model': Author,
            'arg_name': 'author'
        })
        def view(request, author):
            self.assertEqual(author, valid_author)
        
        response = view(request, author=valid_author.pk)
    
    def test_invalid_single_exists_full(self):
        """
        Test a single "model exists" check on an invalid model id, using the
        full config. It should correctly redirect to the given fallback view.
        """
        
        invalid_id = 0
        redirect_view = 'django_goodies.tests.views.author_list'
        redirect_url = reverse(redirect_view)
        request = self.get_request('/django_goodies/test/author_details/')
        
        @verify(redirect_view, {
            'model': Author,
            'arg_name': 'author'
        })
        def view(request, author):
            raise Exception('Shouldn\'t be here')
        
        response = view(request, author=invalid_id)
        self.assertRedirects(response, redirect_url)
    
    ## <-- Single basic "model exists" check ---
    
    ## --- Chained basic "model exists" checks -->
    
    def test_valid_chained_exists_compact(self):
        """
        Test a chain of "model exists" checks on valid model ids, using compact
        configs. It should correctly replace the `author` and `book` arguments
        of the view.
        """
        
        valid_author = self.author
        valid_book = self.book
        request = self.get_request('/django_goodies/test/book_details/')
        
        @verify('django_goodies.tests.views.author_list', (Author, 'author'), (Book, 'book'))
        def view(request, author, book):
            self.assertEqual(author, valid_author)
            self.assertEqual(book, valid_book)
        
        response = view(request, author=valid_author.pk, book=valid_book.pk)
    
    def test_invalid_first_item_chained_exists_compact(self):
        """
        Test a chain of "model exists" checks, using compact configs, failing
        on the first. It should correctly redirect to the given fallback view.
        """
        
        invalid_id = 0
        valid_book = self.book
        redirect_view = 'django_goodies.tests.views.author_list'
        redirect_url = reverse(redirect_view)
        request = self.get_request('/django_goodies/test/book_details/')
        
        @verify(redirect_view, (Author, 'author'), (Book, 'book'))
        def view(request, author, book):
            raise Exception('Shouldn\'t be here')
        
        response = view(request, author=invalid_id, book=valid_book.pk)
        self.assertRedirects(response, redirect_url)
    
    def test_invalid_second_item_chained_exists_compact(self):
        """
        Test a chain of "model exists" checks, using compact configs, failing
        on the second. It should correctly redirect to the given fallback view.
        """
        
        invalid_id = 0
        valid_author = self.author
        redirect_view = 'django_goodies.tests.views.author_list'
        redirect_url = reverse(redirect_view)
        request = self.get_request('/django_goodies/test/book_details/')
        
        @verify(redirect_view, (Author, 'author'), (Book, 'book'))
        def view(request, author, book):
            raise Exception('Shouldn\'t be here')
        
        response = view(request, author=valid_author.pk, book=invalid_id)
        self.assertRedirects(response, redirect_url)
    
    def test_valid_chained_exists_full(self):
        """
        Test a chain of "model exists" checks on valid model ids, using full
        configs. It should correctly replace the `author` and `book` arguments
        of the view.
        """
        
        valid_author = self.author
        valid_book = self.book
        request = self.get_request('/django_goodies/test/book_details/')
        
        author_check = {
            'model': Author,
            'arg_name': 'author'
        }
        
        book_check = {
            'model': Book,
            'arg_name': 'book'
        }
        
        @verify('django_goodies.tests.views.author_list', author_check, book_check)
        def view(request, author, book):
            self.assertEqual(author, valid_author)
            self.assertEqual(book, valid_book)
        
        response = view(request, author=valid_author.pk, book=valid_book.pk)
    
    def test_invalid_first_item_chained_exists_full(self):
        """
        Test a chain of "model exists" checks, using full configs, failing
        on the first. It should correctly redirect to the given fallback view.
        """
        
        invalid_id = 0
        valid_book = self.book
        redirect_view = 'django_goodies.tests.views.author_list'
        redirect_url = reverse(redirect_view)
        request = self.get_request('/django_goodies/test/book_details/')
        
        author_check = {
            'model': Author,
            'arg_name': 'author'
        }
        
        book_check = {
            'model': Book,
            'arg_name': 'book'
        }
        
        @verify(redirect_view, author_check, book_check)
        def view(request, author, book):
            raise Exception('Shouldn\'t be here')
        
        response = view(request, author=invalid_id, book=valid_book.pk)
        self.assertRedirects(response, redirect_url)
    
    def test_invalid_second_item_chained_exists_full(self):
        """
        Test a chain of "model exists" checks, using full configs, failing
        on the second. It should correctly redirect to the given fallback view.
        """
        
        invalid_id = 0
        valid_author = self.author
        redirect_view = 'django_goodies.tests.views.author_list'
        redirect_url = reverse(redirect_view)
        request = self.get_request('/django_goodies/test/book_details/')
        
        author_check = {
            'model': Author,
            'arg_name': 'author'
        }
        
        book_check = {
            'model': Book,
            'arg_name': 'book'
        }
        
        @verify(redirect_view, author_check, book_check)
        def view(request, author, book):
            raise Exception('Shouldn\'t be here')
        
        response = view(request, author=valid_author.pk, book=invalid_id)
        self.assertRedirects(response, redirect_url)
    
    def test_valid_chained_exists_combo(self):
        """
        Test a chain of "model exists" checks on valid model ids, using both
        compact and full configs. It should correctly replace the `author` and
        `book` arguments of the view.
        """
        
        valid_author = self.author
        valid_book = self.book
        request = self.get_request('/django_goodies/test/book_details/')
        
        author_check = {
            'model': Author,
            'arg_name': 'author'
        }
        
        @verify('django_goodies.tests.views.author_list', author_check, (Book, 'book'))
        def view(request, author, book):
            self.assertEqual(author, valid_author)
            self.assertEqual(book, valid_book)
        
        response = view(request, author=valid_author.pk, book=valid_book.pk)
    
    ## <-- Chained basic "model exists" checks ---
    
