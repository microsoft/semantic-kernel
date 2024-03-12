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
"""The command to enable Config Delivery Argo CD Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions


class Enable(base.UpdateCommand, base.EnableCommand):
  """Enable Config Delivery Argo CD Feature on a membership.

  This command enables Config Delivery Argo CD Feature on a membership.

  ## EXAMPLES

  To enable the Config Delivery Argo CD Feature, run:

    $ {command} --config-membership=CONFIG_MEMBERSHIP
  """

  feature_name = 'configdeliveryargocd'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser, flag_override='--config-membership')

  def Run(self, args):
    config_membership = base.ParseMembership(
        args, prompt=True, flag_override='config_membership')

    membership_specs = {
        config_membership: self.messages.MembershipFeatureSpec(
            configDeliveryArgoCd=self.messages.ConfigDeliveryArgoCDMembershipSpec(
                channel=self.messages.ConfigDeliveryArgoCDMembershipSpec.ChannelValueValuesEnum.STABLE,
            )
        )
    }

    feature = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(membership_specs)
    )

    try:
      return self.Update(['membership_specs'], feature)
    except exceptions.Error as e:
      fne = self.FeatureNotEnabledError()
      if str(e) == str(fne):
        return self.Enable(feature)
      else:
        raise e
