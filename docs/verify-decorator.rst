The "verify" decorator
======================

This is a view function decorator that will verify a view argument as a valid id
against a given model. When the id is valid, the argument value will be replaced
by the valid model instance. When the id is not valid, the decorator will issue
a redirect to the configured fallback view.

Usage
-----

The following usage examples assume the following contrived example setup:

.. code-block:: python

    # models.py
    
    class Author(models.Model):
        
        name = models.CharField(max_length=100)
    
    class Book(models.Model):
        
        title = models.CharField(max_length=100)
        author = models.ForeignKey(Author)
    
    
    # views.py
    
    def author_list(request):
        
        # ...snip...
    
    def author_details(request, author):
        
        # ...snip...
    
    def author_book_list(request, author):
        
        # ...snip...
    
    def book_detail(request, author, book):
        
        # ...snip...


Verify a single argument
~~~~~~~~~~~~~~~~~~~~~~~~

For views requiring verification of a single argument, such as the ``author_details``
view, we can decorate it like so:

.. code-block:: python

    from django_goodies.decorators import verify
    
    @verify('myproject.views.author_list', (Author, 'author'))
    def author_details(request, author):
        
        # ...snip...

The first argument to the decorator is the dotted path to the view function
that should be redirected to if the argument is not a valid id. In the above
example, if an invalid Author id is given, the request will be redirected
back to the list of all authors.

The second argument to the decorator is the _verifier_, the configuration object
responsible for controlling how the verification of an argument takes place. In
this example it is a simple two-tuple, ``(Author, author)``. This is the
simplest form of a verifier. In this format, it simply specifies the model to
verify against and the name of the view argument that will contain the id to
verify.

If the verification is successful, the ``author`` argument's value will be
replaced with the valid Author instance, and this will be passed into the
view function in place of the original id.

Verify multiple arguments
~~~~~~~~~~~~~~~~~~~~~~~~~

For views requiring verification of multiple arguments, such as the ``book_detail``
view, we can decorate it like so:

.. code-block:: python

    from django_goodies.decorators import verify
    
    @verify('myproject.views.author_list', (Author, 'author'), (Book, 'book'))
    def book_detail(request, author, book):
        
        # ...snip...

Simply passing extra verifiers to the decorator allows it to verify multiple
arguments.

If _either_ argument fails verification, the request will be redirected to the
``myproject.views.author_list`` view. Otherwise, all verified arguments will
be replaced with the respective valid model instance.
