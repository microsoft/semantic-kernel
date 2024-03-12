#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Setup installation module for gsutil."""

import os

from setuptools import find_packages
from setuptools import setup
from setuptools.command import build_py
from setuptools.command import sdist

long_desc_content_type = 'text/plain'

long_desc = """
gsutil is a Python application that lets you access Google Cloud Storage from
the command line. You can use gsutil to do a wide range of bucket and object
management tasks, including:
 * Creating and deleting buckets.
 * Uploading, downloading, and deleting objects.
 * Listing buckets and objects.
 * Moving, copying, and renaming objects.
 * Editing object and bucket ACLs.
"""

requires = [
    'argcomplete>=1.9.4',
    'crcmod>=1.7',
    'fasteners>=0.14.1',
    'gcs-oauth2-boto-plugin>=3.0',
    'google-apitools>=0.5.32',
    'httplib2==0.20.4',
    'google-reauth>=0.1.0',
    # mock is part of the standard library in Python 3.3 onwards.
    # 3.0.5 is the last version that supports Python 3.3 or lower.
    'mock>=2.0.0, <=3.0.5; python_version < "3.3"',
    'monotonic>=1.4',
    'pyOpenSSL>=0.13',
    'retry_decorator>=1.0.0',
    'six>=1.16.0',
    # aiohttp is the extra dependency that contains requests lib.
    'google-auth[aiohttp]>=2.5.0',
]

CURDIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(CURDIR, 'VERSION'), 'r') as f:
  VERSION = f.read().strip()

with open(os.path.join(CURDIR, 'CHECKSUM'), 'r') as f:
  CHECKSUM = f.read()


def PlaceNeededFiles(self, target_dir):
  """Populates necessary files into the gslib module and unit test modules."""
  target_dir = os.path.join(target_dir, 'gslib')
  self.mkpath(target_dir)

  # Copy the gsutil root VERSION file into gslib module.
  with open(os.path.join(target_dir, 'VERSION'), 'w') as fp:
    fp.write(VERSION)

  # Copy the gsutil root CHECKSUM file into gslib module.
  with open(os.path.join(target_dir, 'CHECKSUM'), 'w') as fp:
    fp.write(CHECKSUM)


class CustomBuildPy(build_py.build_py):
  """Excludes update command from package-installed versions of gsutil."""

  def byte_compile(self, files):
    for filename in files:
      # Note: we exclude the update command here because binary distributions
      # (built via setup.py bdist command) don't abide by the MANIFEST file.
      # For source distributions (built via setup.py sdist), the update command
      # will be excluded by the MANIFEST file.
      if 'gslib/commands/update.py' in filename:
        os.unlink(filename)
    build_py.build_py.byte_compile(self, files)

  def run(self):
    if not self.dry_run:
      PlaceNeededFiles(self, self.build_lib)
      build_py.build_py.run(self)


class CustomSDist(sdist.sdist):

  def make_release_tree(self, base_dir, files):
    sdist.sdist.make_release_tree(self, base_dir, files)
    PlaceNeededFiles(self, base_dir)


setup(
    name='gsutil',
    version=VERSION,
    url='https://cloud.google.com/storage/docs/gsutil',
    download_url='https://cloud.google.com/storage/docs/gsutil_install',
    license='Apache 2.0',
    author='Google Inc.',
    author_email='buganizer-system+187143@google.com',
    description=('A command line tool for interacting with cloud storage '
                 'services.'),
    long_description=long_desc,
    long_description_content_type=long_desc_content_type,
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
    ],
    # Gsutil supports Python 3.5+
    python_requires='!=2.*, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
    platforms='any',
    packages=find_packages(
        exclude=[
            # Packages under third_party are installed separately as
            # dependencies (see the "requires" list above). Note that we do not
            # exclude vendored dependencies (under gslib/vendored), as our
            # vendored versions may differ slightly from the official versions.
            'third_party',
        ],
    ),
    include_package_data=True,
    entry_points={
        'console_scripts': ['gsutil = gslib.__main__:main',],
    },
    install_requires=requires,
    cmdclass={
        'build_py': CustomBuildPy,
        'sdist': CustomSDist,
    },
)
