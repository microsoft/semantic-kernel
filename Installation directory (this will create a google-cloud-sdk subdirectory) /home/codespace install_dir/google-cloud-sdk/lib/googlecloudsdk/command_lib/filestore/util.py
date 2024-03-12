# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Common utility functions for all Cloud Filestore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

V1_API_VERSION = 'v1'
ALPHA_API_VERSION = 'v1p1alpha1'
BETA_API_VERSION = 'v1beta1'

PARENT_TEMPLATE = 'projects/{}/locations/{}'
LOCATION_WILDCARD = '-'


def AddDefaultLocationToListRequest(ref, args, req):
  """Python hook for yaml commands to wildcard the region in list requests."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  if hasattr(args, 'zone'):
    location = args.region or args.zone or LOCATION_WILDCARD
  else:
    location = args.region or LOCATION_WILDCARD

  req.parent = PARENT_TEMPLATE.format(project, location)
  return req


def GetApiVersionFromArgs(args):
  """Return API version based on args."""
  release_track = args.calliope_command.ReleaseTrack()
  if release_track == base.ReleaseTrack.ALPHA:
    return ALPHA_API_VERSION
  if release_track == base.ReleaseTrack.BETA:
    return BETA_API_VERSION
  if release_track == base.ReleaseTrack.GA:
    return V1_API_VERSION
  raise exceptions.UnsupportedReleaseTrackError(release_track)
