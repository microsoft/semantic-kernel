# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for updating organization firewall policy rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewall_policy_rule_utils as rule_utils
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import firewall_policies_utils
from googlecloudsdk.command_lib.compute.firewall_policies import flags
import six


class Update(base.UpdateCommand):
  r"""Updates a Compute Engine firewall policy rule.

  *{command}* is used to update organization firewall policy rules.
  """

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_POLICY_ARG = flags.FirewallPolicyRuleArgument(
        required=True, operation='update'
    )
    cls.FIREWALL_POLICY_ARG.AddArgument(parser)
    flags.AddAction(parser, required=False)
    flags.AddFirewallPolicyId(parser, operation='updated')
    flags.AddSrcIpRanges(parser)
    flags.AddDestIpRanges(parser)
    flags.AddLayer4Configs(parser)
    flags.AddDirection(parser)
    flags.AddEnableLogging(parser)
    flags.AddDisabled(parser)
    flags.AddTargetResources(parser)
    flags.AddTargetServiceAccounts(parser)
    flags.AddSrcThreatIntelligence(parser)
    flags.AddDestThreatIntelligence(parser)
    flags.AddSrcRegionCodes(parser)
    flags.AddDestRegionCodes(parser)
    flags.AddSrcAddressGroups(parser)
    flags.AddDestAddressGroups(parser)
    flags.AddSrcFqdns(parser)
    flags.AddDestFqdns(parser)
    flags.AddSecurityProfileGroup(parser)
    flags.AddTlsInspect(parser)
    flags.AddDescription(parser)
    flags.AddNewPriority(parser, operation='update')
    flags.AddOrganization(parser, required=False)

  def Run(self, args):
    clearable_arg_name_to_field_name = {
        'src_ip_ranges': 'match.srcIpRanges',
        'dest_ip_ranges': 'match.destIpRanges',
        'src_region_codes': 'match.srcRegionCodes',
        'dest_region_codes': 'match.destRegionCodes',
        'src_fqdns': 'match.srcFqdns',
        'dest_fqdns': 'match.destFqdns',
        'src_address_groups': 'match.srcAddressGroups',
        'dest_address_groups': 'match.destAddressGroups',
        'src_threat_intelligence': 'match.srcThreatIntelligences',
        'dest_threat_intelligence': 'match.destThreatIntelligences',
        'security_profile_group': 'securityProfileGroup',
        'target_resources': 'targetResources',
        'target_service_accounts': 'targetServiceAccounts',
    }
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False
    )
    org_firewall_policy = client.OrgFirewallPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower(),
    )
    firewall_policy_rule_client = client.OrgFirewallPolicyRule(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower(),
    )
    cleared_fields = []
    priority = rule_utils.ConvertPriorityToInt(ref.Name())
    src_ip_ranges = []
    dest_ip_ranges = []
    layer4_config_list = []
    target_resources = []
    target_service_accounts = []
    src_address_groups = []
    dest_address_groups = []
    src_fqdns = []
    dest_fqdns = []
    src_region_codes = []
    dest_region_codes = []
    src_threat_intelligence = []
    dest_threat_intelligence = []
    enable_logging = None
    disabled = None
    should_setup_match = False
    traffic_direct = None
    matcher = None
    security_profile_group = None
    tls_inspect = None

    for arg in clearable_arg_name_to_field_name:
      if args.IsKnownAndSpecified(arg) and not args.GetValue(arg):
        cleared_fields.append(clearable_arg_name_to_field_name[arg])

    if args.IsSpecified('src_ip_ranges'):
      src_ip_ranges = args.src_ip_ranges
      should_setup_match = True
    if args.IsSpecified('dest_ip_ranges'):
      dest_ip_ranges = args.dest_ip_ranges
      should_setup_match = True
    if args.IsSpecified('layer4_configs'):
      should_setup_match = True
      layer4_config_list = rule_utils.ParseLayer4Configs(
          args.layer4_configs, holder.client.messages
      )
    if args.IsSpecified('target_resources'):
      target_resources = args.target_resources
    if args.IsSpecified('target_service_accounts'):
      target_service_accounts = args.target_service_accounts
    if args.IsSpecified('src_threat_intelligence'):
      src_threat_intelligence = args.src_threat_intelligence
      should_setup_match = True
    if args.IsSpecified('dest_threat_intelligence'):
      dest_threat_intelligence = args.dest_threat_intelligence
      should_setup_match = True
    if args.IsSpecified('src_region_codes'):
      src_region_codes = args.src_region_codes
      should_setup_match = True
    if args.IsSpecified('dest_region_codes'):
      dest_region_codes = args.dest_region_codes
      should_setup_match = True
    if args.IsSpecified('src_address_groups'):
      src_address_groups = [
          firewall_policies_utils.BuildAddressGroupUrl(
              x, args.organization, org_firewall_policy, args.firewall_policy
          )
          for x in args.src_address_groups
      ]
      should_setup_match = True
    if args.IsSpecified('dest_address_groups'):
      dest_address_groups = [
          firewall_policies_utils.BuildAddressGroupUrl(
              x, args.organization, org_firewall_policy, args.firewall_policy
          )
          for x in args.dest_address_groups
      ]
      should_setup_match = True
    if args.IsSpecified('src_fqdns'):
      src_fqdns = args.src_fqdns
      should_setup_match = True
    if args.IsSpecified('dest_fqdns'):
      dest_fqdns = args.dest_fqdns
      should_setup_match = True
    if args.IsSpecified('security_profile_group'):
      security_profile_group = (
          firewall_policies_utils.BuildSecurityProfileGroupUrl(
              security_profile_group=args.security_profile_group,
              optional_organization=args.organization,
              firewall_policy_client=org_firewall_policy,
              firewall_policy_id=args.firewall_policy,
          )
      )
    elif (
        args.IsSpecified('action')
        and args.action != 'apply_security_profile_group'
    ):
      cleared_fields.append('securityProfileGroup')
    if args.IsSpecified('tls_inspect'):
      tls_inspect = args.tls_inspect
    if args.IsSpecified('enable_logging'):
      enable_logging = args.enable_logging
    if args.IsSpecified('disabled'):
      disabled = args.disabled
    if args.IsSpecified('new_priority'):
      new_priority = rule_utils.ConvertPriorityToInt(args.new_priority)
    else:
      new_priority = priority

    # If need to construct a new matcher.
    if should_setup_match:
      matcher = holder.client.messages.FirewallPolicyRuleMatcher(
          srcIpRanges=src_ip_ranges,
          destIpRanges=dest_ip_ranges,
          layer4Configs=layer4_config_list,
          srcAddressGroups=src_address_groups,
          destAddressGroups=dest_address_groups,
          srcFqdns=src_fqdns,
          destFqdns=dest_fqdns,
          srcRegionCodes=src_region_codes,
          destRegionCodes=dest_region_codes,
          srcThreatIntelligences=src_threat_intelligence,
          destThreatIntelligences=dest_threat_intelligence,
      )
    if args.IsSpecified('direction'):
      if args.direction == 'INGRESS':
        traffic_direct = (
            holder.client.messages.FirewallPolicyRule.DirectionValueValuesEnum.INGRESS
        )
      else:
        traffic_direct = (
            holder.client.messages.FirewallPolicyRule.DirectionValueValuesEnum.EGRESS
        )

    firewall_policy_rule = holder.client.messages.FirewallPolicyRule(
        priority=new_priority,
        action=args.action,
        match=matcher,
        direction=traffic_direct,
        targetResources=target_resources,
        targetServiceAccounts=target_service_accounts,
        description=args.description,
        enableLogging=enable_logging,
        disabled=disabled,
        securityProfileGroup=security_profile_group,
        tlsInspect=tls_inspect,
    )

    firewall_policy_id = firewall_policies_utils.GetFirewallPolicyId(
        firewall_policy_rule_client,
        args.firewall_policy,
        organization=args.organization,
    )

    with holder.client.apitools_client.IncludeFields(cleared_fields):
      return firewall_policy_rule_client.Update(
          priority=priority,
          firewall_policy=firewall_policy_id,
          firewall_policy_rule=firewall_policy_rule,
      )


Update.detailed_help = {
    'EXAMPLES': """\
    To update a rule with priority ``10" in an organization firewall policy
    with ID ``123456789" to change the action to ``allow" and description to
    ``new-example-rule", run:

      $ {command} 10 --firewall-policy=123456789 --action=allow
      --description=new-example-rule
    """,
}
