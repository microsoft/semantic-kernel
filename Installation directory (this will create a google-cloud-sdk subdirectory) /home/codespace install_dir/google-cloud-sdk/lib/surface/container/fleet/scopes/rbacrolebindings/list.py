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
"""Command to show fleet scopes in a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List RBAC RoleBindings in a fleet scope.

  This command can fail for the following reasons:
  * The scope specified does not exist.
  * The user does not have access to the specified scope.

  ## EXAMPLES

  The following command lists RBAC RoleBindings in scope `SCOPE` in
  project `PROJECT_ID`:

    $ {command} --scope=SCOPE --project=PROJECT_ID
  """

  @staticmethod
  def Args(parser):
    # Table formatting
    parser.display_info.AddFormat(util.RB_LIST_FORMAT)
    parser.add_argument(
        '--scope',
        type=str,
        required=True,
        help='Name of the fleet scope to list RBAC RoleBindings from.',
    )

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get()
    if args.IsKnownAndSpecified('scope'):
      return fleetclient.ListScopeRBACRoleBindings(project, args.scope)
    raise calliope_exceptions.RequiredArgumentException(
        'scope', 'Namespace parent is required.'
    )
