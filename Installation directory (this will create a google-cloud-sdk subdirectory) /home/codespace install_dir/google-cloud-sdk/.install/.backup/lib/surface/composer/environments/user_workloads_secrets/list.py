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
"""Command that list user workloads Secrets."""

import textwrap

import frozendict
from googlecloudsdk.api_lib.composer import environments_user_workloads_secrets_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args


_DETAILED_HELP = frozendict.frozendict({'EXAMPLES': textwrap.dedent("""\
          To list user workloads Secrets of the environment named env-1, run:

            $ {command} --environment env-1
        """)})


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListUserWorkloadsSecrets(base.Command):
  """List user workloads Secrets."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser,
        'to list user workloads Secrets',
        positional=False,
    )
    parser.display_info.AddFormat('table[box](name.segment(7),data)')

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    return environments_user_workloads_secrets_util.ListUserWorkloadsSecrets(
        env_resource,
        release_track=self.ReleaseTrack(),
    )
