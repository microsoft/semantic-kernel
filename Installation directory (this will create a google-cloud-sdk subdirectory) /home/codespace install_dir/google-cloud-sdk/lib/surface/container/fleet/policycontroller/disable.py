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
"""The command to disable Policy Controller Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


class Disable(base.UpdateCommand):
  """Disable (Uninstall) Policy Controller.

  Uninstalls Policy Controller.

  ## EXAMPLES

  To uninstall Policy Controller, run:

    $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):

    top_group = parser.add_argument_group(mutex=True)
    flags.no_fleet_default_cfg_flag().AddToParser(top_group)

    cmd_flags = flags.PocoFlags(top_group, 'disable')
    cmd_flags.add_memberships()

  def Run(self, args):
    membership_specs = {}
    poco_not_installed = self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum(
        self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum.INSTALL_SPEC_NOT_INSTALLED
    )

    poco_hub_config = self.messages.PolicyControllerHubConfig(
        installSpec=poco_not_installed
    )

    memberships = base.ParseMembershipsPlural(
        args, prompt=True, prompt_cancel=False, search=True
    )

    for membership in memberships:
      membership_path = membership
      membership_specs[membership_path] = self.messages.MembershipFeatureSpec(
          policycontroller=self.messages.PolicyControllerMembershipSpec(
              policyControllerHubConfig=poco_hub_config
          )
      )

    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs)
    )
    return self.Update(['membership_specs'], patch)
