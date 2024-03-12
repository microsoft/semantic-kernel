# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for Data Catalog taxonomies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.data_catalog import util as api_util
from googlecloudsdk.core import exceptions
import six


class InvalidInlineSourceError(exceptions.Error):
  """Error if a inline source is improperly specified."""


def ProcessTaxonomiesFromYAML(inline_source, version_label):
  """Converts the given inline source dict to the corresponding import request.

  Args:
    inline_source: dict, inlineSource part of the import taxonomy request.
    version_label: string, specifies the version for client.
  Returns:
    GoogleCloudDatacatalogV1beta1ImportTaxonomiesRequest
  Raises:
    InvalidInlineSourceError: If the inline source is invalid.
  """
  messages = api_util.GetMessagesModule(version_label)
  if version_label == 'v1':
    request = messages.GoogleCloudDatacatalogV1ImportTaxonomiesRequest
  else:
    request = messages.GoogleCloudDatacatalogV1beta1ImportTaxonomiesRequest

  try:
    import_request_message = encoding.DictToMessage(
        {'inlineSource': inline_source},
        request)
  except AttributeError:
    raise InvalidInlineSourceError('An error occurred while parsing the '
                                   'serialized taxonomy. Please check your '
                                   'input file.')
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(import_request_message)
  if unrecognized_field_paths:
    error_msg_lines = ['Invalid inline source, the following fields are ' +
                       'unrecognized:']
    error_msg_lines += unrecognized_field_paths
    raise InvalidInlineSourceError('\n'.join(error_msg_lines))
  return import_request_message


def _GetUnrecognizedFieldPaths(message):
  """Returns the field paths for unrecognized fields in the message."""
  errors = encoding.UnrecognizedFieldIter(message)
  unrecognized_field_paths = []
  for edges_to_message, field_names in errors:
    message_field_path = '.'.join(six.text_type(e) for e in edges_to_message)
    for field_name in field_names:
      unrecognized_field_paths.append('{}.{}'.format(
          message_field_path, field_name))
  return sorted(unrecognized_field_paths)
