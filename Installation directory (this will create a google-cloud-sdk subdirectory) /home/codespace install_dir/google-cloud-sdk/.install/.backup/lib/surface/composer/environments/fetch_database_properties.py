# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to trigger a database failover."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args

DETAILED_HELP = {
    'EXAMPLES': """\
      To fetch database properties for the environment named ``environment-1'', run:
      $ {command} environment-1
    """
}


class FetchDatabaseProperties(base.Command):
  """Fetch database properties."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'for which to fetch database properties'
    )

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    release_track = self.ReleaseTrack()

    return environments_api_util.FetchDatabaseProperties(
        env_ref, release_track=release_track
    )
