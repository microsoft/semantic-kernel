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
"""Command to update fleet information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.util.args import labels_util


class Update(base.UpdateCommand):
  """Update a fleet scope RBAC RoleBinding.

  This command can fail for the following reasons:
  * The RoleBinding does not exist in the project.
  * The caller does not have permission to access the RoleBinding.

  ## EXAMPLES

  To update the RBAC RoleBinding `RBRB` in scope `SCOPE` in the active
  project to the `viewer` role:

    $ {command} RBRB --scope=SCOPE --role=viewer

  To update the RBAC RoleBinding `RBRB` in scope `SCOPE` in the active
  project to the user `someone@google.com`:

    $ {command} RBRB --scope=SCOPE --user=someone@google.com
  """

  @classmethod
  def Args(cls, parser):
    resources.AddScopeRBACResourceArg(
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
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    mask = []
    current_rbac_rolebinding = fleetclient.GetScopeRBACRoleBinding(
        resources.RBACResourceName(args)
    )
    for flag in ['role', 'user', 'group']:
      if args.IsKnownAndSpecified(flag):
        mask.append(flag)

    # update GCP labels for namespace resource
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    new_labels = labels_diff.Apply(
        fleetclient.messages.RBACRoleBinding.LabelsValue,
        current_rbac_rolebinding.labels,
    ).GetOrNone()
    if new_labels:
      mask.append('labels')

    # if there's nothing to update, then return
    if not mask:
      return
    return fleetclient.UpdateScopeRBACRoleBinding(
        resources.RBACResourceName(args),
        user=args.user,
        group=args.group,
        role=args.role,
        labels=new_labels,
        mask=','.join(mask),
    )
