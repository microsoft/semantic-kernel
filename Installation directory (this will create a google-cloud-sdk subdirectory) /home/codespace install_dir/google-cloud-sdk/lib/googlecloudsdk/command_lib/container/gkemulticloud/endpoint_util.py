# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.container.gkemulticloud import util as api_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from six.moves.urllib import parse


_VALID_LOCATIONS = frozenset([
    'asia-east2',
    'asia-northeast2',
    'asia-south1',
    'asia-southeast1',
    'asia-southeast2',
    'australia-southeast1',
    'europe-north1',
    'europe-west1',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'europe-west6',
    'europe-west9',
    'me-central2',
    'northamerica-northeast1',
    'southamerica-east1',
    'us-east4',
    'us-west1',
])


def _ValidateLocation(location):
  if location not in _VALID_LOCATIONS:
    locations = list(_VALID_LOCATIONS)
    locations.sort()
    raise exceptions.InvalidArgumentException(
        '--location',
        '{bad_location} is not a valid location. Allowed values:'
        ' [{location_list}].'.format(
            bad_location=location,
            location_list=', '.join("'{}'".format(r) for r in locations),
        ),
    )


def _AppendLocation(endpoint, location):
  scheme, netloc, path, params, query, fragment = parse.urlparse(endpoint)
  netloc = '{}-{}'.format(location, netloc)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))


@contextlib.contextmanager
def GkemulticloudEndpointOverride(location, track=base.ReleaseTrack.GA):
  """Context manager to override the GKE Multi-cloud endpoint temporarily.

  Args:
    location: str, location to use for GKE Multi-cloud.
    track: calliope_base.ReleaseTrack, Release track of the endpoint.

  Yields:
    None.
  """

  original_ep = properties.VALUES.api_endpoint_overrides.gkemulticloud.Get()
  try:
    if not original_ep:
      if not location:
        raise ValueError('A location must be specified.')
      _ValidateLocation(location)
      regional_ep = _GetEffectiveEndpoint(location, track=track)
      properties.VALUES.api_endpoint_overrides.gkemulticloud.Set(regional_ep)
    yield
  finally:
    if not original_ep:
      properties.VALUES.api_endpoint_overrides.gkemulticloud.Set(original_ep)


def _GetEffectiveEndpoint(location, track=base.ReleaseTrack.GA):
  """Returns regional GKE Multi-cloud Endpoint."""
  endpoint = apis.GetEffectiveApiEndpoint(
      api_util.MODULE_NAME, api_util.GetApiVersionForTrack(track)
  )
  return _AppendLocation(endpoint, location)
