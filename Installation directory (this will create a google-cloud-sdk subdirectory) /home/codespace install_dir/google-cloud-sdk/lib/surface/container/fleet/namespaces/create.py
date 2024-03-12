# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to create a fleet namespace."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import deprecation_utils
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.util.apis import arg_utils


@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='447.0.0',
    remove=True,
    alt_command='gcloud fleet scopes namespaces create',
)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a fleet namespace.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The project has a fleet namespace with the same name.
  * The caller does not have permission to access the given project.

  ## EXAMPLES

  To create a fleet namespace with name `NAMESPACE` in the active project, run:

    $ {command} NAMESPACE

  To create a fleet namespace in fleet scope `SCOPE` in project `PROJECT_ID`
  with name
  `NAMESPACE`, run:

    $ {command} NAMESPACE --scope=SCOPE --project=PROJECT_ID
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'NAME',
        type=str,
        help='Name of the fleet namespace to be created. Must comply with'
        ' RFC 1123 (up to 63 characters, alphanumeric and \'-\')')
    resources.AddScopeResourceArg(
        parser,
        '--scope',
        util.VERSION_MAP[cls.ReleaseTrack()],
        scope_help='Name of the fleet scope to create the fleet namespace in.',
    )

  def Run(self, args):
    scope = None
    scope_arg = args.CONCEPTS.scope.Parse()
    if scope_arg is not None:
      scope = scope_arg.RelativeName()
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    return fleetclient.CreateNamespace(args.NAME, scope, project)
