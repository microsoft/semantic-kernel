# Copyright 2014 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io

import setuptools


DEPENDENCIES = ['pyu2f']

OAUTH2CLIENT_EXTRA_DEPENDENCIES = [
    'oauth2client>=2.0.0'
]

EXTRAS = {
    'oauth2client': OAUTH2CLIENT_EXTRA_DEPENDENCIES
}


with io.open('README.rst', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='google-reauth',
    version='0.1.0',
    author='Google',
    author_email='googleapis-publisher@google.com',
    description='Google Reauth Library',
    long_description=long_description,
    url='https://github.com/Google/google-reauth-python',
    packages=setuptools.find_packages(exclude=('tests*', 'system_tests*')),
    install_requires=DEPENDENCIES,
    extras_require=EXTRAS,
    license='Apache 2.0',
    keywords='google auth oauth client reauth',
    classifiers=(
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
    ),
)
