#!/usr/bin/env python

from setuptools import setup, find_packages
from iterparse import __version__

setup(
    name='iterparse',
    version=__version__,
    packages=find_packages(),
    install_requires=(
        'lxml',
    ),
)
