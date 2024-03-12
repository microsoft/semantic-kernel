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

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    import setuptools


setuptools.setup(
    name='pyu2f',
    version='0.1.3',
    description='U2F host library for interacting with a U2F device over USB.',
    long_description='pyu2f is a python based U2F host library for Linux, '
                     'Windows, and MacOS. It provides functionality for '
                     'interacting with a U2F device over USB.',
    url='https://github.com/google/pyu2f/',
    author='Google Inc.',
    author_email='pyu2f-team@google.com',
    # Contained modules and scripts.
    packages=setuptools.find_packages(exclude=["pyu2f.tests", "pyu2f.tests.*"]),
    install_requires=[
        'six',
    ],
    tests_require=[
        'unittest2>=0.5.1',
        'pyfakefs>=2.4',
        'mock>=1.0.1',
    ],
    include_package_data=True,
    platforms=["Windows", "Linux", "OS X", "macOS"],
    # PyPI package information.
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    license='Apache 2.0',
    zip_safe=True,
)
