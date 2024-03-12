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
"""ai-platform models describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import locations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags


_COLLECTION = 'ml.projects.locations'


def _AddDescribeArgs(parser):
  flags.GetLocationResourceArg().AddToParser(parser)
  flags.GetRegionArg().AddToParser(parser)
  parser.display_info.AddFormat('json')


def _Run(args):
  with endpoint_util.MlEndpointOverrides(region=args.region):
    return locations.LocationsClient().Get(args.location)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.DescribeCommand):
  """Display AI Platform capabilities in a location."""

  @staticmethod
  def Args(parser):
    _AddDescribeArgs(parser)

  def Run(self, args):
    return _Run(args)
