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
"""Utilities for operating on different endpoints."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from six.moves.urllib import parse

ML_API_VERSION = 'v1'
ML_API_NAME = 'ml'


def DeriveMLRegionalEndpoint(endpoint, region):
  scheme, netloc, path, params, query, fragment = parse.urlparse(endpoint)
  netloc = '{}-{}'.format(region, netloc)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))


@contextlib.contextmanager
def MlEndpointOverrides(region=None):
  """Context manager to override the AI Platform endpoints for a while.

  Args:
    region: str, region of the AI Platform stack.

  Yields:
    None.
  """
  used_endpoint = GetEffectiveMlEndpoint(region)
  old_endpoint = properties.VALUES.api_endpoint_overrides.ml.Get()
  try:
    log.status.Print('Using endpoint [{}]'.format(used_endpoint))
    if region and region != 'global':
      properties.VALUES.api_endpoint_overrides.ml.Set(used_endpoint)
    yield
  finally:
    old_endpoint = properties.VALUES.api_endpoint_overrides.ml.Set(old_endpoint)


def GetEffectiveMlEndpoint(region):
  """Returns regional ML Endpoint, or global if region not set."""
  endpoint = apis.GetEffectiveApiEndpoint(ML_API_NAME, ML_API_VERSION)
  if region and region != 'global':
    return DeriveMLRegionalEndpoint(endpoint, region)
  return endpoint
