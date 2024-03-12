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
"""Utilities for operating on endpoints for different regions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from six.moves.urllib import parse


def DeriveAiplatformRegionalEndpoint(endpoint, region, is_prediction=False):
  """Adds region as a prefix of the base url."""
  scheme, netloc, path, params, query, fragment = parse.urlparse(endpoint)
  if netloc.startswith('aiplatform'):
    if is_prediction:
      netloc = '{}-prediction-{}'.format(region, netloc)
    else:
      netloc = '{}-{}'.format(region, netloc)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))


@contextlib.contextmanager
def AiplatformEndpointOverrides(version, region, is_prediction=False):
  """Context manager to override the AI Platform endpoints for a while.

  Raises an error if
  region is not set.

  Args:
    version: str, implies the version that the endpoint will use.
    region: str, region of the AI Platform stack.
    is_prediction: bool, it's for prediction endpoint or not.

  Yields:
    None
  """
  used_endpoint = GetEffectiveEndpoint(version=version, region=region,
                                       is_prediction=is_prediction)
  log.status.Print('Using endpoint [{}]'.format(used_endpoint))
  properties.VALUES.api_endpoint_overrides.aiplatform.Set(used_endpoint)
  yield


def GetEffectiveEndpoint(version, region, is_prediction=False):
  """Returns regional AI Platform endpoint, or raise an error if the region not set."""
  endpoint = apis.GetEffectiveApiEndpoint(
      constants.AI_PLATFORM_API_NAME,
      constants.AI_PLATFORM_API_VERSION[version])
  return DeriveAiplatformRegionalEndpoint(
      endpoint, region, is_prediction=is_prediction)
