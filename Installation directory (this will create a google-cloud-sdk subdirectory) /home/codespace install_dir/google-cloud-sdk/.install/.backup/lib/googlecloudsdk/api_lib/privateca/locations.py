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
"""Helpers for dealing with Private CA locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


# The list of locations where the v1 API is available. Used as a fallback in
# case the ListLocations API is down.
_V1Locations = [
    'asia-east1',
    'asia-east2',
    'asia-northeast1',
    'asia-northeast2',
    'asia-northeast3',
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
    'northamerica-northeast1',
    'southamerica-east1',
    'us-central1',
    'us-east1',
    'us-east4',
    'us-west1',
    'us-west2',
    'us-west3',
    'us-west4',
]


def GetSupportedLocations(version='v1'):
  """Gets a list of supported Private CA locations for the current project."""
  if version != 'v1':
    raise exceptions.NotYetImplementedError(
        'Unknown API version: {}'.format(version))

  client = base.GetClientInstance(api_version='v1')
  messages = base.GetMessagesModule(api_version='v1')

  project = properties.VALUES.core.project.GetOrFail()

  try:
    response = client.projects_locations.List(
        messages.PrivatecaProjectsLocationsListRequest(
            name='projects/{}'.format(project)))
    return [location.locationId for location in response.locations]
  except exceptions.HttpError as e:
    log.debug('ListLocations failed: %r.', e)
    log.debug('Falling back to hard-coded list.')
    return _V1Locations
