# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for GCS long-running operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.storage import errors


_BUCKET_OPERATION_NAME_REGEX = r'projects/.+/buckets/(?P<bucket>.+)'
_BUCKET_AND_ID_OPERATION_NAME_REGEX = (
    _BUCKET_OPERATION_NAME_REGEX + r'/operations/(?P<id>.+)'
)


def get_operation_bucket_from_name(operation_name):
  """Extracts operation ID from user input of operation name or ID."""
  m = re.match(_BUCKET_OPERATION_NAME_REGEX, operation_name)
  try:
    return m.group('bucket')
  except AttributeError:
    raise errors.Error(
        'Invalid operation name format. Expected: {} Received: {}'.format(
            _BUCKET_OPERATION_NAME_REGEX, operation_name
        )
    )


def get_operation_bucket_and_id_from_name(operation_name):
  """Extracts operation ID from user input of operation name or ID."""
  m = re.match(_BUCKET_AND_ID_OPERATION_NAME_REGEX, operation_name)
  try:
    return m.group('bucket'), m.group('id')
  except AttributeError:
    raise errors.Error(
        'Invalid operation name format. Expected: {} Received: {}'.format(
            _BUCKET_AND_ID_OPERATION_NAME_REGEX, operation_name
        )
    )
