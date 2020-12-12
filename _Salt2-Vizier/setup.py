#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

requires = ['apache_beam[gcp]',
            'argparse',
            'astropy',
            'astroquery',
            'fastavro',
            'google-cloud-dataflow',
            # 'logging',
            'regions',
            'workflow',
            ]
packages = ['custommods',
            'custommods.data_utils',
            'custommods.vizier_utils',
            ]

setup(
    name = 'vizier-beam',
    version = '0.0.1',
    url = 'https://github.com/mwvgroup/Pitt-Google-Broker',
    author = 'Troy Raen',
    author_email = 'troy.raen@pitt.edu',
    install_requires = requires,
    packages = find_packages(include=packages),
)
