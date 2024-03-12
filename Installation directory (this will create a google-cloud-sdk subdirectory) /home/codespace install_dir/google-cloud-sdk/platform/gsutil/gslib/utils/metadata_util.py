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
"""Shared utility methods for manipulating metadata of requests and resources."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import six
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages


def AddAcceptEncodingGzipIfNeeded(headers_dict, compressed_encoding=False):
  if compressed_encoding:
    # If we send accept-encoding: gzip with a range request, the service
    # may respond with the whole object, which would be bad for resuming.
    # So only accept gzip encoding if the object we are downloading has
    # a gzip content encoding.
    # TODO: If we want to support compressive transcoding fully in the client,
    # condition on whether we are requesting the entire range of the object.
    # In this case, we can accept the first bytes of the object compressively
    # transcoded, but we must perform data integrity checking on bytes after
    # they are decompressed on-the-fly, and any connection break must be
    # resumed without compressive transcoding since we cannot specify an
    # offset. We would also need to ensure that hashes for downloaded data
    # from objects stored with content-encoding:gzip continue to be calculated
    # prior to our own on-the-fly decompression so they match the stored hashes.
    headers_dict['accept-encoding'] = 'gzip'


def CreateCustomMetadata(entries=None, custom_metadata=None):
  """Creates a custom MetadataValue object.

  Inserts the key/value pairs in entries.

  Args:
    entries: (Dict[str, Any] or None) The dictionary containing key/value pairs
        to insert into metadata. Both the key and value must be able to be
        casted to a string type.
    custom_metadata (apitools_messages.Object.MetadataValue or None): A
        pre-existing custom metadata object to add to. If one is not provided,
        a new one will be constructed.

  Returns:
    An apitools_messages.Object.MetadataValue.
  """
  if custom_metadata is None:
    custom_metadata = apitools_messages.Object.MetadataValue(
        additionalProperties=[])
  if entries is None:
    entries = {}
  for key, value in six.iteritems(entries):
    custom_metadata.additionalProperties.append(
        apitools_messages.Object.MetadataValue.AdditionalProperty(
            key=str(key), value=str(value)))
  return custom_metadata


def GetValueFromObjectCustomMetadata(obj_metadata,
                                     search_key,
                                     default_value=None):
  """Filters a specific element out of an object's custom metadata.

  Args:
    obj_metadata: (apitools_messages.Object) The metadata for an object.
    search_key: (str) The custom metadata key to search for.
    default_value: (Any) The default value to use for the key if it cannot be
        found.

  Returns:
    (Tuple(bool, Any)) A tuple indicating if the value could be found in
    metadata and a value corresponding to search_key (the value at the specified
    key in custom metadata, or the default value if the specified key does not
    exist in the custom metadata).
  """
  try:
    value = next((attr.value
                  for attr in obj_metadata.metadata.additionalProperties
                  if attr.key == search_key), None)
    if value is None:
      return False, default_value
    return True, value
  except AttributeError:
    return False, default_value


def IsCustomMetadataHeader(header):
  """Returns true if header (which must be lowercase) is a custom header."""
  return header.startswith('x-goog-meta-') or header.startswith('x-amz-meta-')


def ObjectIsGzipEncoded(obj_metadata):
  """Returns true if the apitools_messages.Object has gzip content-encoding."""
  return (obj_metadata.contentEncoding and
          obj_metadata.contentEncoding.lower().endswith('gzip'))
