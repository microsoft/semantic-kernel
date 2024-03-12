# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""`gcloud access-context-manager levels update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import levels as levels_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import levels
from googlecloudsdk.command_lib.accesscontextmanager import policies

_API_VERSION_PER_TRACK = {'ALPHA': 'v1alpha', 'BETA': 'v1', 'GA': 'v1'}

_FEATURE_MASK_PER_TRACK = {
    'ALPHA': {
        'custom_levels': True
    },
    'BETA': {
        'custom_levels': True
    },
    'GA': {
        'custom_levels': True
    }
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateLevelGA(base.UpdateCommand):
  """Update an existing access level."""

  _API_VERSION = _API_VERSION_PER_TRACK.get('GA')
  _FEATURE_MASK = _FEATURE_MASK_PER_TRACK.get('GA')

  @staticmethod
  def Args(parser):
    UpdateLevelGA.ArgsVersioned(parser, release_track='GA')

  @staticmethod
  def ArgsVersioned(parser, release_track):
    api_version = _API_VERSION_PER_TRACK.get(release_track, 'v1')
    feature_mask = _FEATURE_MASK_PER_TRACK.get(release_track, {})
    levels.AddResourceArg(parser, 'to update')
    levels.AddLevelArgs(parser)
    levels.AddLevelSpecArgs(
        parser, api_version=api_version, feature_mask=feature_mask)

  def Run(self, args):
    client = levels_api.Client(version=self._API_VERSION)

    level_ref = args.CONCEPTS.level.Parse()
    policies.ValidateAccessPolicyArg(level_ref, args)

    basic_level_combine_function = None
    if args.IsSpecified('combine_function'):
      mapper = levels.GetCombineFunctionEnumMapper(
          api_version=self._API_VERSION)
      basic_level_combine_function = mapper.GetEnumForChoice(
          args.combine_function)

    custom_level_expr = None
    if (self._FEATURE_MASK.get('custom_levels', False) and
        args.IsSpecified('custom_level_spec')):
      custom_level_expr = args.custom_level_spec

    return client.Patch(
        level_ref,
        description=args.description,
        title=args.title,
        basic_level_combine_function=basic_level_combine_function,
        basic_level_conditions=args.basic_level_spec,
        custom_level_expr=custom_level_expr)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateLevelBeta(UpdateLevelGA):
  _API_VERSION = _API_VERSION_PER_TRACK.get('BETA')
  _FEATURE_MASK = _FEATURE_MASK_PER_TRACK.get('BETA')

  @staticmethod
  def Args(parser):
    UpdateLevelGA.ArgsVersioned(parser, release_track='BETA')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateLevelAlpha(UpdateLevelGA):
  _API_VERSION = _API_VERSION_PER_TRACK.get('ALPHA')
  _FEATURE_MASK = _FEATURE_MASK_PER_TRACK.get('ALPHA')

  @staticmethod
  def Args(parser):
    UpdateLevelGA.ArgsVersioned(parser, release_track='ALPHA')
