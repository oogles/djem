import re

from setuptools import setup, find_packages
from codecs import open # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Read the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Read the version from djem/__init__.py
version_re = r'^__version__ = [\'"]([^\'"]*)[\'"]'
init_path = path.join(here, 'djem', '__init__.py')
with open(init_path) as f:
    match = re.search(version_re, f.read(), re.MULTILINE)
    if match:
        version = match.group(1)
    else:
        raise RuntimeError('Unable to find __version__ in {0}'.format(init_path))

setup(
    name='djem',
    version=version,
    
    description='A collection of useful stuff for Django projects.',
    long_description=long_description,
    license='BSD',
    
    url='https://github.com/oogles/djem',
    author='Alex Church',
    author_email='alex@church.id.au',
    
    packages=find_packages(exclude=['docs']),
    include_package_data=True,
    
    install_requires=['Django>=2.2'],
    python_requires='>=3.6',
    
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities',
    ]
)
