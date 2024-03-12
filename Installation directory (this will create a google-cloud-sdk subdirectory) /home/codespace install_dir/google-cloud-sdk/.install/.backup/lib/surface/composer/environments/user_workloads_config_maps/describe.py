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
"""Command that gets details about a user workloads ConfigMap."""

import textwrap
import typing
from typing import Union

import frozendict
from googlecloudsdk.api_lib.composer import environments_user_workloads_config_maps_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args

if typing.TYPE_CHECKING:
  from googlecloudsdk.generated_clients.apis.composer.v1alpha2 import composer_v1alpha2_messages
  from googlecloudsdk.generated_clients.apis.composer.v1beta1 import composer_v1beta1_messages
  from googlecloudsdk.generated_clients.apis.composer.v1 import composer_v1_messages


_DETAILED_HELP = frozendict.frozendict({'EXAMPLES': textwrap.dedent("""\
          To get details about a user workloads ConfigMap of the environment named env-1, run:

            $ {command} config-map-1 --environment env-1
        """)})


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DescribeUserWorkloadsConfigMap(base.Command):
  """Get details about a user workloads ConfigMap."""

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

  def Run(self, args) -> Union[
      'composer_v1alpha2_messages.UserWorkloadsConfigMap',
      'composer_v1beta1_messages.UserWorkloadsConfigMap',
      'composer_v1_messages.UserWorkloadsConfigMap',
  ]:
    env_resource = args.CONCEPTS.environment.Parse()
    return (
        environments_user_workloads_config_maps_util.GetUserWorkloadsConfigMap(
            env_resource,
            args.config_map_name,
            release_track=self.ReleaseTrack(),
        )
    )
