#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'salt2-beam',
    version = '0.0.1',
    url = 'https://github.com/mwvgroup/Pitt-Google-Broker',
    author = 'Troy Raen',
    author_email = 'troy.raen@pitt.edu',
    install_requires = ['google-cloud-storage', 'astropy', 'sncosmo', 'iminuit', 'matplotlib'],
    packages = find_packages(),
)
