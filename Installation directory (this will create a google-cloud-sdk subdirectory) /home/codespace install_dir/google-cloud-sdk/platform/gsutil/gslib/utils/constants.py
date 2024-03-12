# -*- coding: utf-8 -*-
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
"""Shared, hard-coded constants.

A constant should not be placed in this file if:
- it requires complicated or conditional logic to initialize.
- it requires importing any modules outside of the Python standard library. This
  helps reduce dependency graph complexity and the chance of cyclic deps.
- it is only used in one file (in which case it should be defined within that
  module).
- it semantically belongs somewhere else (e.g. 'BYTES_PER_KIB' would belong in
  unit_util.py).
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys

import six

from gslib.utils.unit_util import ONE_GIB
from gslib.utils.unit_util import ONE_KIB
from gslib.utils.unit_util import ONE_MIB

# Readable descriptions for httplib2 logging levels.
DEBUGLEVEL_DUMP_REQUESTS = 3
DEBUGLEVEL_DUMP_REQUESTS_AND_PAYLOADS = 4

DEFAULT_FILE_BUFFER_SIZE = 8 * ONE_KIB

DEFAULT_GCS_JSON_API_VERSION = 'v1'

DEFAULT_GSUTIL_STATE_DIR = os.path.expanduser(os.path.join('~', '.gsutil'))

GSUTIL_PUB_TARBALL = 'gs://pub/gsutil.tar.gz'
GSUTIL_PUB_TARBALL_PY2 = 'gs://pub/gsutil4.tar.gz'

IAM_POLICY_VERSION = 3

IMPERSONATE_SERVICE_ACCOUNT = ''

# Number of seconds to wait before printing a long retry warning message.
LONG_RETRY_WARN_SEC = 10

# Compressed transport encoded uploads buffer chunks of compressed data. When
# running many uploads in parallel, compression may consume more memory than
# available. This restricts the number of compressed transport encoded uploads
# running in parallel such that they don't consume more memory than set here.
MAX_UPLOAD_COMPRESSION_BUFFER_SIZE = 2 * ONE_GIB

# On Unix-like systems, we will set the maximum number of open files to avoid
# hitting the limit imposed by the OS. This number was obtained experimentally.
MIN_ACCEPTABLE_OPEN_FILES_LIMIT = 1000

# For files >= this size, output a message indicating that we're running an
# operation on the file (like hashing or gzipping) so it does not appear to the
# user that the command is hanging.
# TODO: This should say the unit in the name.
MIN_SIZE_COMPUTE_LOGGING = 100 * ONE_MIB

# The way NO_MAX is used, what is really needed here is the maximum container
# size in the Python C code, so using six.MAXSIZE which provides that portably.
NO_MAX = six.MAXSIZE

# Number of objects to request in listing calls.
NUM_OBJECTS_PER_LIST_PAGE = 1000

RELEASE_NOTES_URL = 'https://pub.storage.googleapis.com/gsutil_ReleaseNotes.txt'

REQUEST_REASON_ENV_VAR = 'CLOUDSDK_CORE_REQUEST_REASON'
REQUEST_REASON_HEADER_KEY = 'x-goog-request-reason'

RESUMABLE_THRESHOLD_MIB = 8
RESUMABLE_THRESHOLD_B = RESUMABLE_THRESHOLD_MIB * ONE_MIB

# gsutil-specific GUIDs for marking special metadata for S3 compatibility.
S3_ACL_MARKER_GUID = '3b89a6b5-b55a-4900-8c44-0b0a2f5eab43-s3-AclMarker'
S3_DELETE_MARKER_GUID = 'eadeeee8-fa8c-49bb-8a7d-0362215932d8-s3-DeleteMarker'
S3_MARKER_GUIDS = [S3_ACL_MARKER_GUID, S3_DELETE_MARKER_GUID]

# By default, the timeout for SSL read errors is infinite. This could
# cause gsutil to hang on network disconnect, so pick a more reasonable
# timeout.
SSL_TIMEOUT_SEC = 60

# Start with a progress callback every <X> KiB during uploads/downloads (JSON
# API). Callback implementation should back off until it hits some maximum size
# so that callbacks do not create huge amounts of log output.
START_CALLBACK_PER_BYTES = 256 * ONE_KIB

# Upload/download files in 8 KiB chunks over the HTTP connection.
# TODO: This should say the unit in the name.
if 'win32' in str(sys.platform).lower():
  TRANSFER_BUFFER_SIZE = 64 * ONE_KIB
else:
  TRANSFER_BUFFER_SIZE = 8 * ONE_KIB

UTF8 = 'utf-8'

WINDOWS_1252 = 'cp1252'

# Default number of progress callbacks during transfer (XML API).
XML_PROGRESS_CALLBACKS = 10


class Scopes(object):
  """Enum class for auth scopes, as unicode."""
  CLOUD_PLATFORM = 'https://www.googleapis.com/auth/cloud-platform'
  CLOUD_PLATFORM_READ_ONLY = (
      'https://www.googleapis.com/auth/cloud-platform.read-only')
  FULL_CONTROL = 'https://www.googleapis.com/auth/devstorage.full_control'
  READ_ONLY = 'https://www.googleapis.com/auth/devstorage.read_only'
  READ_WRITE = 'https://www.googleapis.com/auth/devstorage.read_write'
  REAUTH = 'https://www.googleapis.com/auth/accounts.reauth'
