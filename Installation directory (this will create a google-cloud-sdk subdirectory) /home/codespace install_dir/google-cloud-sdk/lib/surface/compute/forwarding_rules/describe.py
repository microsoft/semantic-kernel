# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing forwarding rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


def _Args(parser):
  forwarding_rules_arg = flags.ForwardingRuleArgument()
  forwarding_rules_arg.AddArgument(parser, operation_type='describe')
  return forwarding_rules_arg


def _Run(args, holder, forwarding_rules_arg):
  """Issues request necessary to describe the Forwarding Rule."""
  client = holder.client

  forwarding_rule_ref = forwarding_rules_arg.ResolveAsResource(
      args,
      holder.resources,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
    service = client.apitools_client.forwardingRules
    request = client.messages.ComputeForwardingRulesGetRequest(
        **forwarding_rule_ref.AsDict())
  elif forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
    service = client.apitools_client.globalForwardingRules
    request = client.messages.ComputeGlobalForwardingRulesGetRequest(
        **forwarding_rule_ref.AsDict())

  return client.MakeRequests([(service, 'Get', request)])[0]


class Describe(base.DescribeCommand):
  """Display detailed information about a forwarding rule.

  *{command}* displays all data associated with a forwarding rule
  in a project.

  ## EXAMPLES
  To get details about a global forwarding rule, run:

    $ {command} FORWARDING-RULE --global

  To get details about a regional forwarding rule, run:

    $ {command} FORWARDING-RULE --region=us-central1
  """

  FORWARDING_RULE_ARG = None

  @staticmethod
  def Args(parser):
    Describe.FORWARDING_RULE_ARG = _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.FORWARDING_RULE_ARG)
