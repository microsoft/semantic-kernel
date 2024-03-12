# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command that deletes a user workloads ConfigMap."""

import textwrap

import frozendict
from googlecloudsdk.api_lib.composer import environments_user_workloads_config_maps_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.core import log


_DETAILED_HELP = frozendict.frozendict({'EXAMPLES': textwrap.dedent("""\
          To delete a user workloads ConfigMap of the environment named env-1, run:

            $ {command} config-map-1 --environment env-1
        """)})


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteUserWorkloadsConfigMap(base.Command):
  """Delete a user workloads ConfigMap."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    base.Argument(
        'config_map_name', nargs='?', help='Name of the ConfigMap.'
    ).AddToParser(parser)
    resource_args.AddEnvironmentResourceArg(
        parser,
        'of the config_map',
        positional=False,
    )

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    environments_user_workloads_config_maps_util.DeleteUserWorkloadsConfigMap(
        env_resource,
        args.config_map_name,
        release_track=self.ReleaseTrack(),
    )

    log.status.Print('ConfigMap deleted')
