#!/usr/bin/env python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup configuration."""

import platform

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    import setuptools

# Configure the required packages and scripts to install, depending on
# Python version and OS.
REQUIRED_PACKAGES = [
    'httplib2>=0.8',
    'fasteners>=0.14',
    'oauth2client>=1.4.12',
    'six>=1.12.0',
    ]

CLI_PACKAGES = [
    'python-gflags>=3.0.6',
]

TESTING_PACKAGES = [
    'mock>=1.0.1',
]

CONSOLE_SCRIPTS = [
    'gen_client = apitools.gen.gen_client:main',
]

py_version = platform.python_version()

_APITOOLS_VERSION = '0.5.32'

with open('README.rst') as fileobj:
    README = fileobj.read()

setuptools.setup(
    name='google-apitools',
    version=_APITOOLS_VERSION,
    description='client libraries for humans',
    long_description=README,
    url='http://github.com/google/apitools',
    author='Craig Citro',
    author_email='craigcitro@google.com',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    # Contained modules and scripts.
    packages=setuptools.find_packages(include=['apitools']),
    entry_points={'console_scripts': CONSOLE_SCRIPTS},
    install_requires=REQUIRED_PACKAGES,
    tests_require=REQUIRED_PACKAGES + CLI_PACKAGES + TESTING_PACKAGES,
    extras_require={
        'cli': CLI_PACKAGES,
        'testing': TESTING_PACKAGES,
        },
    # Add in any packaged data.
    include_package_data=True,
    package_data={
        'apitools.data': ['*'],
    },
    exclude_package_data={
        '': [
            '*_test.py',
            '*/testing/*',
            '*/testdata/*',
            'base/protorpclite/test_util.py',
            'gen/test_utils.py',
        ],
    },
    # PyPI package information.
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    license='Apache 2.0',
    keywords='apitools',
    )
