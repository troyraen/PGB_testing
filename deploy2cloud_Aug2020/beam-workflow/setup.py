#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

include = [
            'beam_helpers', 
            'beam_helpers.*'
          ]

requires = [
            'apache_beam[gcp]',
            'astropy',
            # 'base64', builtin
            'fastavro',
            'google-cloud-core>=1.4.1',
            'google-cloud-dataflow',
            'google-cloud-datastore>=1.15',
            'google-cloud-storage',
            'iminuit',
            # 'io', builtin
            # 'json', builtin
            'matplotlib',
            'numpy',
            'pandas',
            'sncosmo',
            # 'tempfile', builtin
            'workflow',
            ]

setup(
    name = 'ztf-consumer-beam',
    version = '0.0.1',
    url = 'https://github.com/mwvgroup/Pitt-Google-Broker',
    author = 'Troy Raen',
    author_email = 'troy.raen@pitt.edu',
    install_requires = requires,
    packages = find_packages(include=include),
)
