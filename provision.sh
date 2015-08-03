#!/usr/bin/env bash

apt-get update
apt-get install -y git

# Create downloads directory if it doesn't exist
if [ ! -d downloads ]; then
    mkdir downloads
fi

# Download get-pip.py if it doesn't already exist, install pip
if [ ! -f downloads/get-pip.py ]; then
	cd downloads
    wget https://bootstrap.pypa.io/get-pip.py
	python get-pip.py
	cd ../
fi

# Use pip to install Django
pip install Django

# Install Sphinx for documentation generation
pip install sphinx sphinx-autobuild
