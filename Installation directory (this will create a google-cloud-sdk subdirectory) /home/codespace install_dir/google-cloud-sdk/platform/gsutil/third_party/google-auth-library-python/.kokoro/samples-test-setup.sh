#!/bin/bash
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -eo pipefail

if [[ -z "${PROJECT_ROOT:-}" ]]; then
    PROJECT_ROOT="github/google-auth-library-python"
fi

cd "${PROJECT_ROOT}"

# Disable buffering, so that the logs stream through.
export PYTHONUNBUFFERED=1

# Remove old nox
python3 -m pip uninstall --yes --quiet nox-automation

# Install nox
python3 -m pip install --upgrade --quiet nox
python3 -m nox --version

# Setup service account credentials.
export GOOGLE_APPLICATION_CREDENTIALS=${KOKORO_GFILE_DIR}/service-account.json

# Setup project id.
export PROJECT_ID=$(cat "${KOKORO_GFILE_DIR}/project-id.txt")

# Activate gcloud with service account credentials
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
gcloud config set project ${PROJECT_ID}

# Decrypt system test secrets
./scripts/decrypt-secrets.sh

# Run system tests which use a different noxfile
python3 -m nox -f samples/cloud-client/snippets/noxfile.py
