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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT=$( dirname "$DIR" )

# Work from the project root.
cd $ROOT

gcloud kms decrypt \
  --location=global \
  --keyring=ci \
  --key=kokoro-secrets \
  --ciphertext-file=system_tests/secrets.tar.enc \
  --plaintext-file=system_tests/secrets.tar
tar xvf system_tests/secrets.tar
rm system_tests/secrets.tar
