#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

requires = ['apache_beam[gcp]',
            'google-cloud-dataflow',
            'workflow',
            # 'io',
            'fastavro',
            # 'tempfile',  'astropy', 'sncosmo', 'iminuit'
            ]

setup(
    name = 'ztf-consumer-beam',
    version = '0.0.1',
    url = 'https://github.com/mwvgroup/Pitt-Google-Broker',
    author = 'Troy Raen',
    author_email = 'troy.raen@pitt.edu',
    install_requires = requires,
    # packages = find_packages(include=['beam_helpers', 'beam_helpers.*']),
)
