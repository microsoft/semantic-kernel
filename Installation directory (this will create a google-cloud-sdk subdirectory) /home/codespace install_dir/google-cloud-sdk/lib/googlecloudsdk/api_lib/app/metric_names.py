# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Appengine CSI metric names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# Metric names for CSI

# Reserved CSI metric prefix for appengine
_APPENGINE_PREFIX = 'app_deploy_'

# "Start" suffix
START = '_start'

# Time to upload project source tarball to GCS
CLOUDBUILD_UPLOAD = _APPENGINE_PREFIX + 'cloudbuild_upload'
CLOUDBUILD_UPLOAD_START = CLOUDBUILD_UPLOAD + START

# Time to execute Argo Cloud Build request
CLOUDBUILD_EXECUTE = _APPENGINE_PREFIX + 'cloudbuild_execute'
CLOUDBUILD_EXECUTE_START = CLOUDBUILD_EXECUTE + START
CLOUDBUILD_EXECUTE_ASYNC = CLOUDBUILD_EXECUTE + '_async'
CLOUDBUILD_EXECUTE_ASYNC_START = CLOUDBUILD_EXECUTE_ASYNC + START

# Time to copy application files to the application code bucket
COPY_APP_FILES = _APPENGINE_PREFIX + 'copy_app_files'
COPY_APP_FILES_START = COPY_APP_FILES + START

# Time to copy application files to the application code bucket without gsutil.
# No longer used, but may still come in from old versions.
COPY_APP_FILES_NO_GSUTIL = _APPENGINE_PREFIX + 'copy_app_files_no_gsutil'

# Time for a deploy using appengine API
DEPLOY_API = _APPENGINE_PREFIX + 'deploy_api'
DEPLOY_API_START = DEPLOY_API + START

# Time for API request to get the application code bucket.
GET_CODE_BUCKET = _APPENGINE_PREFIX + 'get_code_bucket'
GET_CODE_BUCKET_START = GET_CODE_BUCKET + START

# Time for setting deployed version to default using appengine API
SET_DEFAULT_VERSION_API = (_APPENGINE_PREFIX + 'set_default_version_api')
SET_DEFAULT_VERSION_API_START = SET_DEFAULT_VERSION_API + START

# Time for API request to prepare environment for VMs.
PREPARE_ENV = _APPENGINE_PREFIX + 'prepare_environment'
PREPARE_ENV_START = PREPARE_ENV + START

# Time to update config files.
UPDATE_CONFIG = _APPENGINE_PREFIX + 'update_config'
UPDATE_CONFIG_START = UPDATE_CONFIG + START

# First service deployment
FIRST_SERVICE_DEPLOY = _APPENGINE_PREFIX + 'first_service_deploy'
FIRST_SERVICE_DEPLOY_START = FIRST_SERVICE_DEPLOY + START
