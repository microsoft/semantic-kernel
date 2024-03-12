#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

if __name__ == '__main__':
    setup(name='rsa',
          version='4.5',
          description='Pure-Python RSA implementation',
          long_description=long_description,
          long_description_content_type='text/markdown',
          author='Sybren A. Stuvel',
          author_email='sybren@stuvel.eu',
          maintainer='Sybren A. Stuvel',
          maintainer_email='sybren@stuvel.eu',
          url='https://stuvel.eu/rsa',
          packages=['rsa'],
          license='ASL 2',
          classifiers=[
              'Development Status :: 5 - Production/Stable',
              'Intended Audience :: Developers',
              'Intended Audience :: Education',
              'Intended Audience :: Information Technology',
              'License :: OSI Approved :: Apache Software License',
              'Operating System :: OS Independent',
              'Programming Language :: Python',
              'Programming Language :: Python :: 2',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: 3.6',
              'Programming Language :: Python :: 3.7',
              'Programming Language :: Python :: Implementation :: CPython',
              'Programming Language :: Python :: Implementation :: PyPy',
              'Topic :: Security :: Cryptography',
          ],
          python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
          install_requires=[
              'pyasn1 >= 0.1.3',
          ],
          entry_points={'console_scripts': [
              'pyrsa-priv2pub = rsa.util:private_to_public',
              'pyrsa-keygen = rsa.cli:keygen',
              'pyrsa-encrypt = rsa.cli:encrypt',
              'pyrsa-decrypt = rsa.cli:decrypt',
              'pyrsa-sign = rsa.cli:sign',
              'pyrsa-verify = rsa.cli:verify',
          ]},

          )
