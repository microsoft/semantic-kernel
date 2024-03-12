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
"""Command to show fleet namespaces in a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet import util


class List(base.ListCommand):
  """List fleet namespaces in a project.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The user does not have access to the project specified.

  ## EXAMPLES

  The following command lists namespaces in the active project:

    $ {command}

  The following command lists namespaces in project `PROJECT_ID`:

    $ {command} --project=PROJECT_ID
  """

  @classmethod
  def Args(cls, parser):
    # Table formatting
    parser.display_info.AddFormat(util.SC_NS_LIST_FORMAT)
    resources.AddScopeResourceArg(
        parser,
        '--scope',
        api_util.VERSION_MAP[cls.ReleaseTrack()],
        scope_help='Name of the fleet scope to list fleet namespaces from.',
        required=True,
    )

  def Run(self, args):
    scope_arg = args.CONCEPTS.scope.Parse()
    scope_path = scope_arg.RelativeName()
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    return fleetclient.ListScopeNamespaces(scope_path)
