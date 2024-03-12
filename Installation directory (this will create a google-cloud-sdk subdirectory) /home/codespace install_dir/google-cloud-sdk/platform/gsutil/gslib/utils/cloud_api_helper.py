# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Helper functions for Cloud API implementations."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import json
import re

import six

from gslib.cloud_api import ArgumentException
from gslib.utils.text_util import AddQueryParamToUrl


def GetCloudApiInstance(cls, thread_state=None):
  """Gets a gsutil Cloud API instance.

  Since Cloud API implementations are not guaranteed to be thread-safe, each
  thread needs its own instance. These instances are passed to each thread
  via the thread pool logic in command.

  Args:
    cls: Command class to be used for single-threaded case.
    thread_state: Per thread state from this thread containing a gsutil
                  Cloud API instance.

  Returns:
    gsutil Cloud API instance.
  """
  return thread_state or cls.gsutil_api


def GetDownloadSerializationData(src_obj_metadata,
                                 progress=0,
                                 user_project=None):
  """Returns download serialization data.

  There are five entries:
    auto_transfer: JSON-specific field, always False.
    progress: How much of the download has already been completed.
    total_size: Total object size.
    url: Implementation-specific field used for saving a metadata get call.
         For JSON, this the download URL of the object.
         For XML, this is a pickled boto key.
    user_project: Project to be billed to, added as query param.

  Args:
    src_obj_metadata: Object to be downloaded.
    progress: See above.
    user_project: User project to add to query string.

  Returns:
    Serialization data for use with Cloud API GetObjectMedia.
  """

  url = src_obj_metadata.mediaLink
  if user_project:
    url = AddQueryParamToUrl(url, 'userProject', user_project)

  if six.PY3:
    if isinstance(url, bytes):
      url = url.decode('ascii')

  serialization_dict = {
      'auto_transfer': 'False',
      'progress': progress,
      'total_size': src_obj_metadata.size,
      'url': url
  }

  return json.dumps(serialization_dict)


def ListToGetFields(list_fields=None):
  """Removes 'items/' from the input fields and converts it to a set.

  Args:
    list_fields: Iterable fields usable in ListBuckets/ListObjects calls.

  Returns:
    Set of fields usable in GetBucket/GetObjectMetadata calls (None implies
    all fields should be returned).
  """
  if list_fields:
    get_fields = set()
    for field in list_fields:
      if field in ('kind', 'nextPageToken', 'prefixes'):
        # These are not actually object / bucket metadata fields.
        # They are fields specific to listing, so we don't consider them.
        continue
      get_fields.add(re.sub(r'items/', '', field))
    return get_fields


def ValidateDstObjectMetadata(dst_obj_metadata):
  """Ensures dst_obj_metadata supplies the needed fields for copy and insert.

  Args:
    dst_obj_metadata: Metadata to validate.

  Raises:
    ArgumentException if metadata is invalid.
  """
  if not dst_obj_metadata:
    raise ArgumentException(
        'No object metadata supplied for destination object.')
  if not dst_obj_metadata.name:
    raise ArgumentException(
        'Object metadata supplied for destination object had no object name.')
  if not dst_obj_metadata.bucket:
    raise ArgumentException(
        'Object metadata supplied for destination object had no bucket name.')
