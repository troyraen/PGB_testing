#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup #, find_packages

setup(
    name = 'rubin-alert-stream-simulator',
    version = '0.0.1',
    url = 'https://github.com/mwvgroup/Pitt-Google-Broker',
    author = 'Troy Raen',
    author_email = 'troy.raen@pitt.edu',
    install_requires = ['apache_beam', 'lsst.alert.stream'],
    # packages = find_packages(),
)
