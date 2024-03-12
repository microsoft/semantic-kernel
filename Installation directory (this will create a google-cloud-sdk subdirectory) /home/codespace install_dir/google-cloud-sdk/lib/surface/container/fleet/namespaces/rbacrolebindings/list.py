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
"""Command to show fleet namespaces in a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib import deprecation_utils
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.core import properties


@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='447.0.0',
    remove=True,
    alt_command='gcloud fleet scopes rbacrolebindings list',
)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List RBAC RoleBindings in a fleet namespace.

  This command can fail for the following reasons:
  * The namespace specified does not exist.
  * The user does not have access to the specified namespace.

  ## EXAMPLES

  The following command lists RBAC RoleBindings in namespace `NAMESPACE` in
  project `PROJECT_ID`:

    $ {command} --namespace=NAMESPACE --project=PROJECT_ID

  """

  @staticmethod
  def Args(parser):
    # Table formatting
    parser.display_info.AddFormat(util.RB_LIST_FORMAT)
    parser.add_argument(
        '--namespace',
        type=str,
        required=True,
        help='Name of the fleet namespace to list RBAC RoleBindings from.')

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get()
    if args.IsKnownAndSpecified('namespace'):
      return fleetclient.ListRBACRoleBindings(project, args.namespace)
    raise calliope_exceptions.RequiredArgumentException(
        'namespace', 'Namespace parent is required.')
