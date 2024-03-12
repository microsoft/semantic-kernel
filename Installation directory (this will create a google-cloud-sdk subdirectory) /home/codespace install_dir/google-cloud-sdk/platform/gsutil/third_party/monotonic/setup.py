# -*- coding: utf-8 -*-
"""
monotonic
~~~~~~~~~

This module provides a ``monotonic()`` function which returns the
value (in fractional seconds) of a clock which never goes backwards.

On Python 3.3 or newer, ``monotonic`` will be an alias of
``time.monotonic`` from the standard library. On older versions,
it will fall back to an equivalent implementation:

+------------------+----------------------------------------+
| Linux, BSD, AIX  | ``clock_gettime(3)``                   |
+------------------+----------------------------------------+
| Windows          | ``GetTickCount`` or ``GetTickCount64`` |
+------------------+----------------------------------------+
| OS X             | ``mach_absolute_time``                 |
+------------------+----------------------------------------+

If no suitable implementation exists for the current platform,
attempting to import this module (or to import from it) will
cause a ``RuntimeError`` exception to be raised.

"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='monotonic',
    version='1.4',
    license='Apache',
    author='Ori Livneh',
    author_email='ori@wikimedia.org',
    url='https://github.com/atdt/monotonic',
    description='An implementation of time.monotonic() for Python 2 & < 3.3',
    long_description=__doc__,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    py_modules=('monotonic',),
)
