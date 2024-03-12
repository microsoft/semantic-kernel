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
"""Utilities for handling location flag."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from six.moves.urllib import parse

CRM_API_NAME = 'cloudresourcemanager'
CRM_API_VERSION = 'v3'
CRM_STAGING_GLOBAL_API = (
    'https://staging-cloudresourcemanager.sandbox.googleapis.com/')
CRM_STAGING_REGIONAL_SUFFIX = (
    'stagqual-cloudresourcemanager.sandbox.googleapis.com/')

# A few zones are too long to fit into the API name character limit,
# so we truncated them.
LOCATION_MAPPING = {
    'northamerica-northeast2-staginga': 'nane2staginga',
    'northamerica-northeast2-stagingb': 'nane2stagingb',
    'northamerica-northeast2-stagingc': 'nane2stagingc'
}


@contextlib.contextmanager
def CrmEndpointOverrides(location):
  """Context manager to override the current CRM endpoint.

  The new endpoint will temporarily be the one corresponding to the given
  location.

  Args:
    location: str, location of the CRM backend (e.g. a cloud region or zone).
      Can be None to indicate global.

  Yields:
    None.
  """
  endpoint_property = getattr(properties.VALUES.api_endpoint_overrides,
                              CRM_API_NAME)
  old_endpoint = endpoint_property.Get()
  is_staging_env = old_endpoint and (CRM_STAGING_REGIONAL_SUFFIX in old_endpoint
                                     or CRM_STAGING_GLOBAL_API == old_endpoint)
  try:
    if location and location != 'global':
      if is_staging_env:
        # Staging endpoints are formatted differently from other envs due to
        # length; manually set the correct staging regional endpoint value.
        location = LOCATION_MAPPING.get(location, location)
        endpoint_property.Set(
            _DeriveCrmRegionalEndpoint('https://' + CRM_STAGING_REGIONAL_SUFFIX,
                                       location.replace('-', '')))
      else:
        endpoint_property.Set(_GetEffectiveCrmEndpoint(location))
    elif is_staging_env:
      # Manually override global endpoint for staging. (Use gcloud config value
      # for other environments that need the global location.)
      endpoint_property.Set(CRM_STAGING_GLOBAL_API)
    yield
  finally:
    endpoint_property.Set(old_endpoint)


def _GetEffectiveCrmEndpoint(location):
  """Returns regional Tag Bindings Endpoint based on the regional location."""
  endpoint = apis.GetEffectiveApiEndpoint(CRM_API_NAME, CRM_API_VERSION)
  return _DeriveCrmRegionalEndpoint(endpoint, location)


def _DeriveCrmRegionalEndpoint(endpoint, location):
  scheme, netloc, path, params, query, fragment = parse.urlparse(endpoint)
  netloc = '{}-{}'.format(location, netloc)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))
