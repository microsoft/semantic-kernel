# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Package Setup for the Google Cloud ML SDK.
"""

import os
from setuptools import find_packages
from setuptools import setup


def get_required_install_packages():
  global_names = {}
  # pylint: disable=exec-used
  with open(os.path.normpath('google/cloud/ml/version.py')) as f:
    exec(f.read(), global_names)
  return global_names['required_install_packages']


def get_version():
  global_names = {}
  # pylint: disable=exec-used
  with open(os.path.normpath('google/cloud/ml/version.py')) as f:
    exec(f.read(), global_names)
  return global_names['__version__']


setup(
    name='cloudml',
    version=get_version(),
    author='Google',
    author_email='cloudml-feedback@google.com',
    namespace_packages=['google', 'google.cloud'],
    install_requires=get_required_install_packages(),
    packages=find_packages(),
    include_package_data=True,
    description='Google Cloud Machine Learning Prediction SDK',
    requires=[])
