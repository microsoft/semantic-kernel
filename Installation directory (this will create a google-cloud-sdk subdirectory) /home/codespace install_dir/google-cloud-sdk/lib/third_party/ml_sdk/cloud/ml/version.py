# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Cloud ML Engine Prediction version constants.
"""

# Google Cloud Machine Learning Prediction Engine Version info.
__version__ = '0.1-alpha'

required_install_packages = [
    'oauth2client >= 2.2.0',
    'six >= 1.10.0, < 2.0',
    'bs4 >= 0.0.1, < 1.0',
    'numpy >= 1.10.4',  # Don't pin numpy, as it requires a recompile.
    'crcmod >= 1.7, < 2.0',
    'nltk >= 3.2.1, <= 3.4',
    'pyyaml >= 3.11, < 7.0',
    'protobuf >= 3.1.0, < 4.0',
    # isort is avro dependency which picks the latest.
    # We do not want use latest because of b/160639883.
    'isort < 5.0',
    # Python 3.7 seems incompatible with enum34. See b/148202403.
    'enum34 >= 1.1; python_version <= "3.5"',
]

required_install_packages_with_batch_prediction = required_install_packages + [
    # Remove < 2.4.0 after b/77730826 is fixed.
    'apache-beam[gcp] >= 2.0.0, < 2.4.0',
    'google-cloud-logging >= 0.23.0, < 1.0',
]

required_install_packages_no_deps = required_install_packages + [
    'google-cloud-logging >= 0.23.0, <=1.15.0',
    'google-api-python-client <= 1.9.0',
]
