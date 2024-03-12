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
"""Describe Policy Controller feature command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import protos
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


class Describe(base.DescribeCommand, command.PocoCommand):
  """Describe Policy Controller feature.

  ## EXAMPLES

  To describe the Policy Controller feature:

      $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = flags.PocoFlags(parser, 'describe')
    cmd_flags.add_memberships()

  def Run(self, args):
    feature = self.GetFeature()

    if args.memberships is not None:
      specs = self.path_specs(args, ignore_metadata=False)
      feature.membershipSpecs = protos.set_additional_properties(
          self.messages.Feature.MembershipSpecsValue(), specs
      )

      states = self.path_states(args)
      feature.membershipStates = protos.set_additional_properties(
          self.messages.Feature.MembershipStatesValue(), states
      )

    return feature
