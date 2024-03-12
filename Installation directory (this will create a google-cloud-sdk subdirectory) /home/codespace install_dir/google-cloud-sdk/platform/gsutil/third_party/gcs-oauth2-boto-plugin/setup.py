#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc.
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

"""Setup installation module for gcs-oauth2-boto-plugin."""

from setuptools import find_packages
from setuptools import setup

long_desc = """
gcs-oauth2-boto-plugin is a Python application whose purpose is to behave as an
auth plugin for the boto auth plugin framework for use with OAuth 2.0
credentials for the Google Cloud Platform. This plugin is compatible with both
user accounts and service accounts, and its functionality is essentially a
wrapper around oauth2client with the addition of automatically caching tokens
for the machine in a thread- and process-safe fashion.
"""

requires = [
    'rsa==4.7.2',
    'boto>=2.29.1',
    'google-reauth>=0.1.0',
    'httplib2>=0.18',
    'oauth2client>=2.2.0',
    'pyOpenSSL>=0.13',
    'retry_decorator>=1.0.0',
    'six>=1.12.0'
]

extras_require = {
    'dev': [
        'freezegun',
        'mock;python_version<"3.3"',
    ],
}

setup(
    name='gcs-oauth2-boto-plugin',
    version='3.0',
    url='https://developers.google.com/storage/docs/gspythonlibrary',
    download_url=('https://github.com/GoogleCloudPlatform'
                  '/gcs-oauth2-boto-plugin'),
    license='Apache 2.0',
    author='Google Inc.',
    author_email='gs-team@google.com',
    description=('Auth plugin allowing use the use of OAuth 2.0 credentials '
                 'for Google Cloud Storage in the Boto library.'),
    long_description=long_desc,
    zip_safe=True,
    platforms='any',
    packages=find_packages(exclude=['third_party']),
    include_package_data=True,
    install_requires=requires,
    extras_require=extras_require,
    tests_require=extras_require['dev'],
    test_suite='gcs_oauth2_boto_plugin.test_oauth2_client',
    classifiers=[
        'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
