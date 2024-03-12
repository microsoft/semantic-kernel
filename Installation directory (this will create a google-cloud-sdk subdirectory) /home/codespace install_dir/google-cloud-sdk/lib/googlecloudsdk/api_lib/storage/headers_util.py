# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for parsing and validating additional headers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core import properties


# This list comes from gsutil:
# https://github.com/GoogleCloudPlatform/gsutil/blob/master/gslib/utils/translation_helper.py#L74
_METADATA_HEADERS = frozenset({
    'cache-control',
    'content-disposition',
    'content-encoding',
    'content-language',
    'content-md5',
    'content-type',
    'custom-time',
    'x-goog-api-version',
    'x-goog-if-generation-match',
    'x-goog-if-metageneration-match',
})


_METADATA_HEADER_PREFIXES = frozenset({
    'x-goog-meta-',
    'x-amz-meta-',
})


def _remove_metadata_headers(headers_dict):
  """Filters out some headers that correspond to metadata fields.

  It's not necessarily important that all headers corresponding to metadata
  fields are filtered here, but failing to do so for some (e.g. content-type)
  can lead to bugs if the user's setting overrides values set by our API
  client that are required for it to function properly.

  Args:
    headers_dict (dict): Header key:value pairs provided by the user.

  Returns:
    A dictionary with a subset of the pairs in headers_dict -- those matching
    some metadata fields are filtered out.
  """
  filtered_headers = {}
  for header, value in headers_dict.items():
    header_matches_metadata_prefixes = (
        header.startswith(prefix) for prefix in _METADATA_HEADER_PREFIXES)
    if (header not in _METADATA_HEADERS and
        not any(header_matches_metadata_prefixes)):
      filtered_headers[header] = value
  return filtered_headers


def get_additional_header_dict():
  """Gets a dictionary of headers for API calls based on a property value."""
  headers_string = properties.VALUES.storage.additional_headers.Get()
  if not headers_string:
    return {}

  parser = arg_parsers.ArgDict()
  headers_dict = parser(headers_string)
  return _remove_metadata_headers(headers_dict)
