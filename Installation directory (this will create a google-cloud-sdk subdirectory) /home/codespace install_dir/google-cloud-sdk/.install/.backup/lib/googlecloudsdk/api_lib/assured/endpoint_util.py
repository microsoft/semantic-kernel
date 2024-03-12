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
"""Utilities for regionalizing Assured Workloads API endpoints."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import re

from googlecloudsdk.api_lib.assured import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from six.moves.urllib import parse


ENV_NETLOC_REGEX_PATTERN = r'((staging|autopush|dev)-)?(assuredworkloads.*)'


@contextlib.contextmanager
def AssuredWorkloadsEndpointOverridesFromRegion(release_track, region):
  """Context manager to regionalize Assured endpoints using a provided region.

  Args:
    release_track: str, Release track of the command being called.
    region: str, Region to use for regionalizing the Assured endpoint.

  Yields:
    None.
  """
  used_endpoint = GetEffectiveAssuredWorkloadsEndpoint(release_track, region)
  old_endpoint = properties.VALUES.api_endpoint_overrides.assuredworkloads.Get()
  try:
    log.status.Print('Using endpoint [{}]'.format(used_endpoint))
    if region:
      properties.VALUES.api_endpoint_overrides.assuredworkloads.Set(
          used_endpoint)
    yield
  finally:
    old_endpoint = properties.VALUES.api_endpoint_overrides.assuredworkloads.Set(
        old_endpoint)


def GetEffectiveAssuredWorkloadsEndpoint(release_track, region):
  """Returns regional Assured Workloads endpoint, or global if region not set."""
  endpoint = apis.GetEffectiveApiEndpoint(util.API_NAME,
                                          util.GetApiVersion(release_track))
  if region:
    return DeriveAssuredWorkloadsRegionalEndpoint(endpoint, region)
  return endpoint


def DeriveAssuredWorkloadsRegionalEndpoint(endpoint, region):
  scheme, netloc, path, params, query, fragment = parse.urlparse(endpoint)
  m = re.match(ENV_NETLOC_REGEX_PATTERN, netloc)
  env = m.group(1)
  netloc_suffix = m.group(3)
  if env:
    netloc = '{}{}-{}'.format(env, region, netloc_suffix)
  else:
    netloc = '{}-{}'.format(region, netloc_suffix)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))
