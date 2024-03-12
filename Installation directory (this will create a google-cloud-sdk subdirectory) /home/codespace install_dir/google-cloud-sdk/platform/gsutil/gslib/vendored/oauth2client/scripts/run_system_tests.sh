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


# If we're on Travis, we need to set up the environment.
if [[ "${TRAVIS}" == "true" ]]; then
  # If secure variables are available, run system test.
  if [[ "${TRAVIS_SECURE_ENV_VARS}" ]]; then
    echo "Running in Travis, decrypting stored key file."
    # Convert encrypted JSON key file into decrypted file to be used.
    openssl aes-256-cbc -K ${OAUTH2CLIENT_KEY} \
        -iv ${OAUTH2CLIENT_IV} \
        -in tests/data/key.json.enc \
        -out ${OAUTH2CLIENT_TEST_JSON_KEY_PATH} -d
    # Convert encrypted P12 key file into decrypted file to be used.
    openssl aes-256-cbc -K ${OAUTH2CLIENT_KEY} \
        -iv ${OAUTH2CLIENT_IV} \
        -in tests/data/key.p12.enc \
        -out ${OAUTH2CLIENT_TEST_P12_KEY_PATH} -d
    # Convert encrypted User JSON key file into decrypted file to be used.
    openssl aes-256-cbc -K ${encrypted_1ee98544e5ca_key} \
        -iv ${encrypted_1ee98544e5ca_iv} \
        -in tests/data/user-key.json.enc \
        -out ${OAUTH2CLIENT_TEST_USER_KEY_PATH} -d
  else
    echo "Running in Travis during non-merge to master, doing nothing."
    exit
  fi
fi

# Run the system tests for each tested package.
python scripts/run_system_tests.py
