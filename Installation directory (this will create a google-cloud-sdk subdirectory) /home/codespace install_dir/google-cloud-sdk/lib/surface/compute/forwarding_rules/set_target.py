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
"""Command for modifying the target of forwarding rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


class SetTargetHelper(object):
  """Helper that sets a forwarding rule's target."""

  FORWARDING_RULE_ARG = None

  def __init__(self, holder, include_regional_tcp_proxy):
    self._holder = holder
    self._include_regional_tcp_proxy = include_regional_tcp_proxy

  @classmethod
  def Args(cls, parser, include_regional_tcp_proxy):
    """Adds flags to set the target of a forwarding rule."""
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    flags.AddSetTargetArgs(
        parser,
        include_regional_tcp_proxy=include_regional_tcp_proxy)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)

  def Run(self, args):
    """Issues requests necessary to set target on Forwarding Rule."""
    client = self._holder.client

    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        self._holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
      requests = self.CreateGlobalRequests(client, self._holder.resources,
                                           forwarding_rule_ref, args)
    elif forwarding_rule_ref.Collection() == 'compute.forwardingRules':
      requests = self.CreateRegionalRequests(client, self._holder.resources,
                                             forwarding_rule_ref, args)

    return client.MakeRequests(requests)

  def CreateGlobalRequests(self, client, resources, forwarding_rule_ref, args):
    """Create a globally scoped request."""
    target_ref = utils.GetGlobalTarget(resources, args)

    request = client.messages.ComputeGlobalForwardingRulesSetTargetRequest(
        forwardingRule=forwarding_rule_ref.Name(),
        project=forwarding_rule_ref.project,
        targetReference=client.messages.TargetReference(
            target=target_ref.SelfLink(),),
    )

    return [(client.apitools_client.globalForwardingRules, 'SetTarget', request)
           ]

  def CreateRegionalRequests(self, client, resources, forwarding_rule_ref,
                             args):
    """Create a regionally scoped request."""
    target_ref, _ = utils.GetRegionalTarget(
        client,
        resources,
        args,
        forwarding_rule_ref=forwarding_rule_ref,
        include_regional_tcp_proxy=self._include_regional_tcp_proxy)

    request = client.messages.ComputeForwardingRulesSetTargetRequest(
        forwardingRule=forwarding_rule_ref.Name(),
        project=forwarding_rule_ref.project,
        region=forwarding_rule_ref.region,
        targetReference=client.messages.TargetReference(
            target=target_ref.SelfLink(),),
    )

    return [(client.apitools_client.forwardingRules, 'SetTarget', request)]


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Set(base.UpdateCommand):
  """Modify a forwarding rule to direct network traffic to a new target."""

  FORWARDING_RULE_ARG = None
  _include_regional_tcp_proxy = True

  detailed_help = {
      'DESCRIPTION': ("""
          *{{command}}* is used to set a new target for a forwarding
          rule. {overview}

          When creating a forwarding rule, exactly one of  ``--target-instance'',
          ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
          ``--target-grpc-proxy'', ``--target-ssl-proxy'',
          ``--target-tcp-proxy'' or ``--target-vpn-gateway''
          must be specified.""".format(overview=flags.FORWARDING_RULES_OVERVIEW)
                     ),
  }

  @classmethod
  def Args(cls, parser):
    SetTargetHelper.Args(parser, cls._include_regional_tcp_proxy)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return SetTargetHelper(holder, self._include_regional_tcp_proxy).Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetBeta(Set):
  """Modify a forwarding rule to direct network traffic to a new target."""
  _include_regional_tcp_proxy = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAlpha(SetBeta):
  """Modify a forwarding rule to direct network traffic to a new target."""
  _include_regional_tcp_proxy = True
