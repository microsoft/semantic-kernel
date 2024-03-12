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
"""Contains Helper Functions for overwatch."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from six import text_type
from six.moves.urllib import parse

INVALID_LOCATION_MESSAGE = ('The location in overwatch path "{}" does not '
                            'match the default location parameter "{}" '
                            'specified at scc/slz-overwatch-location.')


def base_64_encoding(file_path=None, blueprint_plan_=None):
  """Encodes content of a blueprint plan to base64 bytes.

  Args:
    file_path: The path of the blueprint plan file to be encoded.
    blueprint_plan_: The string of the blueprint json file.

  Returns:
    bytes of the message.
  """
  if blueprint_plan_ is None:
    blueprint_plan_ = files.ReadFileContents(file_path)
  return blueprint_plan_.encode()


def derive_regional_endpoint(endpoint, region):
  """Parse the endpoint and add region to it.

  Args:
    endpoint: The url endpoint of the API.
    region: The region for which the endpoint is required.

  Returns:
    regional endpoint for the provided region.
  """
  scheme, netloc, path, params, query, fragment = [
      text_type(el) for el in parse.urlparse(endpoint)
  ]
  # Value of netloc obtained by unparsing url could be,
  # 1. securedlandingzone.googleapis.com
  # 2. {env}-securedlandingzone.googleapis.com
  # For regional endpoint the respective values should be,
  # 1. {region}-securedlandingzone.googleapis.com
  # 2. {env}-{region}-securedlandingzone.googleapis.com
  elem = netloc.split('-')
  elem.insert(len(elem) - 1, region)
  netloc = '-'.join(elem)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))


@contextlib.contextmanager
def override_endpoint(location):
  """Set api_endpoint_overrides property to use the regional endpoint.

  Args:
    location: The location used for the regional endpoint. (optional)

  Yields:
    None
  """
  old_endpoint = apis.GetEffectiveApiEndpoint('securedlandingzone', 'v1beta')
  try:
    if location != 'global':
      # Use regional Endpoint
      regional_endpoint = derive_regional_endpoint(old_endpoint, location)
      properties.VALUES.api_endpoint_overrides.securedlandingzone.Set(
          regional_endpoint)
    yield
  finally:
    properties.VALUES.api_endpoint_overrides.securedlandingzone.Set(
        old_endpoint)
