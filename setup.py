from setuptools import setup, find_packages
from codecs import open # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Execute the django_goodies/__init__.py file to get the version
execfile('django_goodies/__init__.py')

setup(
    name='django-goodies',
    version=__version__,

    description='A collection of useful stuff for Django projects.',
    long_description=long_description,
    license='BSD',

    packages=[
        'django_goodies'
    ],

    url='https://github.com/oogles/django-goodies',
    author='Alex Church',
    author_email='alex@church.id.au'
)
