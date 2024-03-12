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

# If in the pypy environment, activate the never version of pypy provided by
# pyenv.
if [[ "${TOX_ENV}" == "pypy" ]]; then
    PATH="${HOME}/.pyenv/versions/pypy-2.6.0/bin:${PATH}"
    export PATH
fi

tox -e ${TOX_ENV}
