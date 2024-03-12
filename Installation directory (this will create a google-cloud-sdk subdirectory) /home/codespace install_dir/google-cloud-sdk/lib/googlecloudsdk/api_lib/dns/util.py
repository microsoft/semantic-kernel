# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Common utility functions for the dns tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def AppendTrailingDot(name):
  return name if not name or name.endswith('.') else name + '.'


# Camel case to snake case utils
_first_cap_re = re.compile('(.)([A-Z][a-z0-9]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def CamelCaseToSnakeCase(name):
  s1 = _first_cap_re.sub(r'\1_\2', name)
  return _all_cap_re.sub(r'\1_\2', s1).upper()


def GetRegistry(version):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('dns', version)
  return registry


def GetApiFromTrack(track):
  if track == base.ReleaseTrack.BETA:
    return 'v1beta2'
  if track == base.ReleaseTrack.ALPHA:
    return 'v1alpha2'
  if track == base.ReleaseTrack.GA:
    return 'v1'


def GetApiClient(version):
  return apis.GetClientInstance('dns', version)


# Prepare necessary parameters for registry to return the correct resource name.
def GetParamsForRegistry(version, args, parent=None):
  params = {'project': properties.VALUES.core.project.GetOrFail}
  if version == 'v2':
    params['location'] = args.location
  if parent is not None:
    if parent == 'managedZones':
      params['managedZone'] = args.zone
    if parent == 'responsePolicies':
      params['responsePolicy'] = args.response_policy
  return params


def GetApiFromTrackAndArgs(track, args):
  if args.IsSpecified('location'):
    # Has specified a zone, use v2 api
    return 'v2'
  else:
    # Has not specified a zone, use a v1 api depending on the version track.
    return GetApiFromTrack(track)
