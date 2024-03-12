#!/bin/bash

# Copyright 2015 Google Inc. All rights reserved.
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

set -ev

pip install --upgrade pip setuptools tox coveralls

# App Engine tests require the App Engine SDK.
if [[ "${TOX_ENV}" == "gae" || "${TOX_ENV}" == "cover" ]]; then
    pip install gcp-devrel-py-tools
    gcp-devrel-py-tools download-appengine-sdk `dirname ${GAE_PYTHONPATH}`
fi

# Travis ships with an old version of PyPy, so install at least version 2.6.
if [[ "${TOX_ENV}" == "pypy" ]]; then
    if [ ! -d "${HOME}/.pyenv/bin" ]; then
        git clone https://github.com/yyuu/pyenv.git ${HOME}/.pyenv
    fi
    ${HOME}/.pyenv/bin/pyenv install --skip-existing pypy-2.6.0
fi
