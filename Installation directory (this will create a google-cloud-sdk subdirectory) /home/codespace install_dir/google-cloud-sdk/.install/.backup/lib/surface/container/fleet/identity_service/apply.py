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
"""The command to update Identity Service Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.identity_service import utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import retry


# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To apply an Identity Service configuration to a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME --config=/path/to/identity-service.yaml

    To create or modify a fleet-level default membership configuration, run:

    $ {command} --fleet-default-member-config=/path/to/identity-service.yaml

    To apply an existing fleet-level default membership configuration to a membership, run:

    $ {command} --origin=fleet --membership=MEMBERSHIP_NAME
"""


class Apply(base.UpdateCommand):
  """Update the Identity Service Feature.

  This command updates the Identity Service Feature in a fleet.
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'identityservice'

  @classmethod
  def Args(cls, parser):
    command_args = parser.add_group(required=True, mutex=False)
    command_args.add_argument(
        '--fleet-default-member-config',
        type=str,
        help='The path to an identity-service.yaml configuration file.',
        required=False,
    )
    per_member_config_args = command_args.add_group(required=False, mutex=False)
    resources.AddMembershipResourceArg(per_member_config_args)

    per_member_config_source = per_member_config_args.add_group(
        mutex=True, required=True
    )
    per_member_config_source.add_argument(
        '--config',
        type=str,
        help='The path to an identity-service.yaml configuration file.',
    )
    per_member_config_source.add_argument(
        '--origin',
        choices=['fleet'],
        type=str,
        help=(
            'Applies the fleet-level default membership configuration to a'
            ' membership.'
        ),
    )

  def Run(self, args):
    patch = self.messages.Feature()
    update_mask = []

    if args.config or args.origin:
      self.preparePerMemberConfigPatch(args, patch, update_mask)

    if args.fleet_default_member_config:
      self.prepareFleetDefaultMemberConfigPatch(args, patch, update_mask)

    try:
      max_wait_ms = 60000  # 60 secs
      retryer = retry.Retryer(
          max_wait_ms=max_wait_ms, exponential_sleep_multiplier=1.1
      )
      retryer.RetryOnException(
          self.Update, args=(update_mask, patch), sleep_ms=1000
      )
    except retry.MaxRetrialsException:
      raise exceptions.Error(
          'Retry limit exceeded while waiting for the {} feature to update'
          .format(self.feature.display_name)
      )

  def prepareFleetDefaultMemberConfigPatch(self, args, patch, update_mask):
    # Load the config YAML file.
    loaded_config = file_parsers.YamlConfigFile(
        file_path=args.fleet_default_member_config,
        item_type=file_parsers.LoginConfigObject,
    )

    # Create a new identity service feature spec.
    member_config = utils.parse_config(loaded_config, self.messages)

    # Add the fleet default member config to the feature patch and update
    # `update mask`.
    patch.fleetDefaultMemberConfig = (
        self.messages.CommonFleetDefaultMemberConfigSpec(
            identityservice=member_config
        )
    )
    update_mask.append('fleet_default_member_config')

  def preparePerMemberConfigPatch(self, args, patch, update_mask):
    # Get the membership the user is attempting to apply the configuration to.
    # If no membership is specified, and there is a single membership available
    # in the fleet, it would be automatically selected.
    # If no membership is specified, and there are multiple memberships
    # available in the fleet, the user would be prompted to select
    # one from the ones available in the fleet.
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )
    membership_spec = self.messages.MembershipFeatureSpec()
    if args.origin:
      membership_spec.origin = self.messages.Origin(
          type=self.messages.Origin.TypeValueValuesEnum('FLEET')
      )
    else:
      # Load the config YAML file.
      loaded_config = file_parsers.YamlConfigFile(
          file_path=args.config, item_type=file_parsers.LoginConfigObject
      )

      # Create a new identity service feature spec.
      member_config = utils.parse_config(loaded_config, self.messages)
      membership_spec.identityservice = member_config

    # Add the newly prepared membershipSpec to the feature patch and update
    # `update mask`.
    patch.membershipSpecs = self.hubclient.ToMembershipSpecs(
        {membership: membership_spec}
    )
    update_mask.append('membership_specs')
