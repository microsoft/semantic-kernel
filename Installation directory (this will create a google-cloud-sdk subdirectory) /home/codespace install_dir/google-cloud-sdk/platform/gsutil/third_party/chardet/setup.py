#!/usr/bin/env python
import re

from setuptools import find_packages, setup


# Get version without importing, which avoids dependency issues
def get_version():
    with open('chardet/version.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='chardet',
      version=get_version(),
      description='Universal encoding detector for Python 2 and 3',
      long_description=readme(),
      author='Mark Pilgrim',
      author_email='mark@diveintomark.org',
      maintainer='Daniel Blanchard',
      maintainer_email='dan.blanchard@gmail.com',
      url='https://github.com/chardet/chardet',
      license="LGPL",
      keywords=['encoding', 'i18n', 'xml'],
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: Developers",
                   ("License :: OSI Approved :: GNU Library or Lesser General"
                    " Public License (LGPL)"),
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   ("Topic :: Software Development :: Libraries :: Python "
                    "Modules"),
                   "Topic :: Text Processing :: Linguistic"],
      packages=find_packages(),
      setup_requires=['pytest-runner'],
      tests_require=['pytest', 'hypothesis'],
      entry_points={'console_scripts':
                    ['chardetect = chardet.cli.chardetect:main']})
