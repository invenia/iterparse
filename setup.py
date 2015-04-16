#!/usr/bin/env python

from setuptools import setup, find_packages
import re

package_name = 'iterparse'

version = ''
with open('{}/__init__.py'.format(package_name), 'r') as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*?)[\'"]',
        f.read(), re.MULTILINE,
    ).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name=package_name,
    version=version,
    packages=find_packages(),
    install_requires=(
        'lxml',
    ),
)
