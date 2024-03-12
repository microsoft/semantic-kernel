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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base


class Delete(base.UpdateCommand):
  """Delete a resource from the Identity Service Feature.

  Deletes a resource from the Identity Service Feature.

  ## EXAMPLES

  To delete the Identity Service configuration from a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME

  To delete the fleet-level default membership configuration, run:

    $ {command} --fleet-default-member-config
  """

  feature_name = 'identityservice'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser, membership_help='Membership name provided during registration.')
    parser.add_argument(
        '--fleet-default-member-config',
        action='store_true',
        help="""If specified, deletes the default membership
        configuration present in your fleet.

        To delete the default membership configuration present in your
        fleet, run:

          $ {command} --fleet-default-member-config""",
    )

  def Run(self, args):
    update_mask = []
    patch = self.messages.Feature()

    if args.fleet_default_member_config:
      update_mask.append('fleet_default_member_config')
      if not args.membership:
        # TODO: b/307330225) - Figure out a way to get rid of this.
        # This is currently necessary because the Hub CLH doesn't currently
        # allow updates with an empty FeatureSpec object. `spec` isn't actually
        # going to get updated as it isn't present in the update mask.
        patch.spec = self.messages.CommonFeatureSpec()

        self.Update(update_mask, patch)
        return

    self.preparePerMemberConfigDeletion(args, update_mask, patch)
    self.Update(update_mask, patch)

  def preparePerMemberConfigDeletion(self, args, mask, patch):
    # Get the membership the user is trying to delete a config from.
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True)

    patch.membershipSpecs = self.hubclient.ToMembershipSpecs(
        {membership: self.messages.MembershipFeatureSpec()}
    )
    mask.append('membership_specs')
