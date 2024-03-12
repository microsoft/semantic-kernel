#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
import sys

doclines = """A collection of ASN.1-based protocols modules.

   A collection of ASN.1 modules expressed in form of pyasn1 classes.
   Includes protocols PDUs definition (SNMP, LDAP etc.) and various
   data structures (X.509, PKCS etc.).
"""

doclines = [x.strip() for x in doclines.split('\n') if x]


classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Information Technology
Intended Audience :: System Administrators
Intended Audience :: Telecommunications Industry
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python :: 2
Programming Language :: Python :: 2.4
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Communications
Topic :: System :: Monitoring
Topic :: System :: Networking :: Monitoring
Topic :: Software Development :: Libraries :: Python Modules
"""


def howto_install_setuptools():
    print("""
   Error: You need setuptools Python package!

   It's very easy to install it, just type (as root on Linux):

   wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
   python ez_setup.py

   Then you could make eggs from this package.
""")


if sys.version_info[:2] < (2, 4):
    print("ERROR: this package requires Python 2.4 or later!")
    sys.exit(1)

try:
    from setuptools import setup, Command

    params = {
        'zip_safe': True,
        'install_requires': ['pyasn1>=0.4.1,<0.5.0']
    }

except ImportError:
    for arg in sys.argv:
        if 'egg' in arg:
            howto_install_setuptools()
            sys.exit(1)

    from distutils.core import setup, Command

    if sys.version_info[:2] > (2, 4):
        params = {
            'requires': ['pyasn1(>=0.4.1,<0.5.0)']
        }
    else:
        params = {
            'requires': ['pyasn1']
        }

params.update(
    {'name': 'pyasn1-modules',
     'version': open('pyasn1_modules/__init__.py').read().split('\'')[1],
     'description': doclines[0],
     'long_description': ' '.join(doclines[1:]),
     'maintainer': 'Ilya Etingof <etingof@gmail.com>',
     'author': 'Ilya Etingof',
     'author_email': 'etingof@gmail.com',
     'url': 'https://github.com/etingof/pyasn1-modules',
     'platforms': ['any'],
     'classifiers': [x for x in classifiers.split('\n') if x],
     'license': 'BSD',
     'packages': ['pyasn1_modules']}
)


# handle unittest discovery feature
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().loadTestsFromNames(
            ['tests.__main__.suite']
        )

        unittest.TextTestRunner(verbosity=2).run(suite)

params['cmdclass'] = {
    'test': PyTest,
    'tests': PyTest
}

setup(**params)
