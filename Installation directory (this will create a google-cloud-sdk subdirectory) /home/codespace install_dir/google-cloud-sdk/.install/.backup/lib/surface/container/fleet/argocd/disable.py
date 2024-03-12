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
"""The command to disable Config Delivery Argo CD Feature on a membership."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base


class Disable(base.UpdateCommand, base.DisableCommand):
  """Disable Config Delivery Argo CD Feature on a membership.

  This command disables Config Delivery Argo CD Feature on a membership.

  ## EXAMPLES

  To disable the Config Delivery Argo CD Feature on a membership, run:

    $ {command} --config-membership=CONFIG_MEMBERSHIP
  """

  feature_name = 'configdeliveryargocd'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser, flag_override='--config-membership')

  def Run(self, args):
    # Get the feature to ensure the feature is enabled
    # Error will be raised if feature is not enabled
    self.GetFeature()

    config_membership = base.ParseMembership(
        args, prompt=True, flag_override='config_membership')

    membership_specs = {}
    membership_specs[config_membership] = self.messages.MembershipFeatureSpec(
        configDeliveryArgoCd=None
    )

    feature = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs)
    )

    feature = self.Update(['membership_specs'], feature)

    # Disable the feature if feature is no longer enabled for any memberships
    if feature.membershipSpecs is None:
      return self.Disable(False)

    return feature
