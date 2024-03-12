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
"""Command that updates a user workloads Secret."""

import textwrap

import frozendict
from googlecloudsdk.api_lib.composer import environments_user_workloads_secrets_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.core import log


_DETAILED_HELP = frozendict.frozendict({'EXAMPLES': textwrap.dedent("""\
          To update a user workloads Secret of the environment named env-1, run:

            $ {command} --environment env-1 --secret-file-path=secret.yaml
        """)})


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateUserWorkloadsSecret(base.Command):
  """Update a user workloads Secret."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser,
        'where the user workloads Secret must be updated',
        positional=False,
    )
    parser.add_argument(
        '--secret-file-path',
        type=str,
        help=(
            'Path to a local file with a single Kubernetes Secret in YAML'
            ' format.'
        ),
        required=True,
    )

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    response = (
        environments_user_workloads_secrets_util.UpdateUserWorkloadsSecret(
            env_resource,
            args.secret_file_path,
            release_track=self.ReleaseTrack(),
        )
    )

    log.status.Print(f'Secret {response.name} updated')
