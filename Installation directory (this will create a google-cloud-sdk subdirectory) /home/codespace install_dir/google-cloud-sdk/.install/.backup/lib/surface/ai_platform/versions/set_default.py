# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""ai-platform versions set-default command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import region_util
from googlecloudsdk.command_lib.ml_engine import versions_util


def _AddSetDefaultArgs(parser):
  flags.GetModelName(positional=False, required=True).AddToParser(parser)
  flags.GetRegionArg(include_global=True).AddToParser(parser)
  flags.VERSION_NAME.AddToParser(parser)


def _Run(args):
  region = region_util.GetRegion(args)
  with endpoint_util.MlEndpointOverrides(region=region):
    client = versions_api.VersionsClient()
    return versions_util.SetDefault(client, args.version, model=args.model)


_DETAILED_HELP = {
    'DESCRIPTION':
        """\
Sets an existing AI Platform version as the default for its model.

*{command}* sets an existing AI Platform version as the default for its
model.  Only one version may be the default for a given version.
"""
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetDefault(base.DescribeCommand):
  """Sets an existing AI Platform version as the default for its model."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _AddSetDefaultArgs(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SetDefaultBeta(SetDefault):
  """Sets an existing AI Platform version as the default for its model."""

  @staticmethod
  def Args(parser):
    _AddSetDefaultArgs(parser)

  def Run(self, args):
    return _Run(args)
