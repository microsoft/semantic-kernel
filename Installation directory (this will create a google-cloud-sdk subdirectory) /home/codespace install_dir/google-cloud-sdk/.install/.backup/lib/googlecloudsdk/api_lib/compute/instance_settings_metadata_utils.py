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
"""Convenience functions for dealing with instance settings metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


UPDATE_MASK_METADATA_PREFIX = 'metadata.items.'


def ConstructInstanceSettingsMetadataMessage(message_classes, metadata):
  is_metadata = message_classes.InstanceSettingsMetadata().ItemsValue()
  if metadata.items():
    for key, value in metadata.items():
      is_metadata.additionalProperties.append(
          is_metadata.AdditionalProperty(key=key, value=value)
      )
  return message_classes.InstanceSettingsMetadata(items=is_metadata)


def ConstructUpdateMask(metadata_keys):
  mask_fields = [
      UPDATE_MASK_METADATA_PREFIX + key.lower() for key in metadata_keys
  ]
  return ','.join(mask_fields)


def ConstructMetadataDict(metadata_msg):
  res = {}
  if metadata_msg:
    for metadata in metadata_msg.items.additionalProperties:
      res[metadata.key] = metadata.value
  return res


def IsRequestMetadataSameAsExistingMetadata(
    request_metadata, existing_metadata
):
  for key, value in request_metadata.items():
    if key not in existing_metadata or value != existing_metadata[key]:
      return False
  return True
