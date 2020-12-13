#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'ztf-consumer-beam',
    version = '0.0.1',
    url = 'https://github.com/mwvgroup/Pitt-Google-Broker',
    author = 'Troy Raen',
    author_email = 'troy.raen@pitt.edu',
    # install_requires = ['astropy', 'sncosmo', 'iminuit'],
    packages = find_packages(),
    package_data = {'config': ['krb5.conf', 'pitt-reader.user.keytab']}
)
