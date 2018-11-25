#!/usr/bin/env bash
# Project-specific version specifications used by the provisioning process

# The Python version to use for the project virtualenv. Leave blank to use the
# system version.
# Define an explicit version: BASE_PYTHON_VERSION='3.6.4'
BASE_PYTHON_VERSION='3.7.1'

# List of additional Python versions to install (e.g. test with multiple
# versions via tox). If not included in the list, BASE_PYTHON_VERSION will be
# appended to the end.
# Define explicit versions: PYTHON_VERSIONS=('2.7.14' '3.5.4' '3.6.4')
PYTHON_VERSIONS=('2.7.15'  '3.4.9'  '3.5.6'  '3.6.7')

# Node.js version (major version only - the latest minor version will always be used)
NODE_VERSION='8'
