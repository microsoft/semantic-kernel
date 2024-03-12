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
"""Command to update fleet information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import deprecation_utils
from googlecloudsdk.command_lib.container.fleet import resources


@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='447.0.0',
    remove=True,
    alt_command='gcloud fleet scopes rbacrolebindings update',
)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update a fleet namespace RBAC RoleBinding.

  This command can fail for the following reasons:
  * The RoleBinding does not exist in the project.
  * The caller does not have permission to access the RoleBinding.

  ## EXAMPLES

  To update the RBAC RoleBinding `RBRB` in namespace `NAMESPACE` in the active
  project to the `viewer` role:

    $ {command} RBRB --namespace=NAMESPACE --role=viewer

  To update the RBAC RoleBinding `RBRB` in namespace `NAMESPACE` in the active
  project to the user `someone@google.com`:

    $ {command} RBRB --namespace=NAMESPACE --user=someone@google.com

  """

  @classmethod
  def Args(cls, parser):
    resources.AddRBACResourceArg(
        parser,
        api_version=util.VERSION_MAP[cls.ReleaseTrack()],
        rbacrb_help=(
            'Name of the RBAC RoleBinding to be updated. '
            'Must comply with RFC 1123 (up to 63 characters, '
            "alphanumeric and '-')"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--user',
        type=str,
        help='User for the RBACRoleBinding to update to.',
    )
    group.add_argument(
        '--group',
        type=str,
        help='Group for the RBACRoleBinding to update to.',
    )
    parser.add_argument(
        '--role',
        choices=['admin', 'edit', 'view'],
        help='Role for the RBACRoleBinding to update to.',
    )

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    mask = []
    for flag in ['role', 'user', 'group']:
      if args.IsKnownAndSpecified(flag):
        mask.append(flag)
    return fleetclient.UpdateRBACRoleBinding(
        resources.RBACResourceName(args),
        user=args.user,
        group=args.group,
        role=args.role,
        mask=','.join(mask))
