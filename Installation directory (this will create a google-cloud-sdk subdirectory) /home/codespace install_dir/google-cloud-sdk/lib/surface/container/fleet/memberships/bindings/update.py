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
"""Command to update Membership Binding information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.util.args import labels_util


class Update(base.UpdateCommand):
  """Update the Binding in a Membership.

  This command can fail for the following reasons:
  * The Membership specified does not exist.
  * The Binding does not exist in the Membership.
  * The caller does not have permission to access the Membership/Binding.
  * The Scope specified does not exist.
  * The caller did not specify the location (--location) if referring to
  location other than global.

  ## EXAMPLES

  To update the binding `BINDING_NAME` in global membership `MEMBERSHIP_NAME`
  in the active project:

    $ {command} BINDING_NAME --membership=MEMBERSHIP_NAME

  To update a Binding `BINDING_NAME` associated with regional membership
  `MEMBERSHIP_NAME`, provide the location LOCATION_NAME for the Membership where
  the Binding belongs along with membership name and associated
  Scope `SCOPE_NAME`.

  $ {command} BINDING_NAME --membership=MEMBERSHIP_NAME --scope=SCOPE_NAME
    --location=LOCATION_NAME

  """

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipBindingResourceArg(
        parser,
        api_version=util.VERSION_MAP[cls.ReleaseTrack()],
        binding_help=(
            'Name of the Membership Binding to be updated.'
            'Must comply with RFC 1123 (up to 63 characters, '
            "alphanumeric and '-')"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    resources.AddScopeResourceArg(
        parser,
        flag_name='--scope',
        api_version=util.VERSION_MAP[cls.ReleaseTrack()],
        scope_help='The Fleet Scope to bind the membership to.',
        group=group,
    )
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    mask = []
    current_binding = fleetclient.GetMembershipBinding(
        resources.MembershipBindingResourceName(args)
    )

    # update GCP labels for namespace resource
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    new_labels = labels_diff.Apply(
        fleetclient.messages.MembershipBinding.LabelsValue,
        current_binding.labels,
    ).GetOrNone()
    if new_labels:
      mask.append('labels')

    for flag in ['fleet', 'scope']:
      if args.IsKnownAndSpecified(flag):
        mask.append(flag)
    scope = None
    if args.CONCEPTS.scope.Parse() is not None:
      scope = args.CONCEPTS.scope.Parse().RelativeName()
    # if there's nothing to update, then return
    if not mask:
      return
    return fleetclient.UpdateMembershipBinding(
        resources.MembershipBindingResourceName(args),
        scope=scope,
        labels=new_labels,
        mask=','.join(mask))
