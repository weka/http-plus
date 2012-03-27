#!/usr/bin/env python
import os
import re
import subprocess
import sys
import time
if not hasattr(sys, 'version_info') or sys.version_info < (2, 4, 0, 'final'):
    raise SystemExit("httpplus requires python 2.4 or later.")

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='httpplus',
    version='0.5',
    url='http://code.google.com/p/py-nonblocking-http',
    license='GNU GPL',
    author='Augie Fackler',
    author_email='durin42@gmail.com',
    description=('httpplus is an enhanced version of httplib with a similar API.'),
#    long_description=open(os.path.join(os.path.dirname(__file__),
#                                         'README')).read(),
    keywords='http',
    packages=('httpplus', 'httpplus.tests'),
    platforms='any',
    classifiers=[
        'License :: OSI Approved :: Apache 2',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
)
