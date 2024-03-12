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
"""Common classes and functions for firewall rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import re

from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions

ALLOWED_METAVAR = 'PROTOCOL[:PORT[-PORT]]'
LEGAL_SPECS = re.compile(
    r"""

    (?P<protocol>[a-zA-Z0-9+.-]+) # The protocol group.

    (:(?P<ports>\d+(-\d+)?))?     # The optional ports group.
                                  # May specify a range.

    $                             # End of input marker.
    """, re.VERBOSE)
EFFECTIVE_FIREWALL_LIST_FORMAT = """\
  table(
    type,
    firewall_policy_name,
    priority,
    action,
    direction,
    disabled,
    ip_ranges.list():label=IP_RANGES
  )"""

LIST_NOTICE = """\
To show all fields of the firewall, please show in JSON format: --format=json
To show more fields in table format, please see the examples in --help.
"""


class ArgumentValidationError(exceptions.Error):
  """Raised when a user specifies --rules and --allow parameters together."""

  def __init__(self, error_message):
    super(ArgumentValidationError, self).__init__(error_message)


class ActionType(enum.Enum):
  """Firewall Action type."""
  ALLOW = 1
  DENY = 2


def AddCommonArgs(parser,
                  for_update=False,
                  with_egress_support=False,
                  with_service_account=False):
  """Adds common arguments for firewall create or update subcommands."""

  min_length = 0 if for_update else 1
  if not for_update:
    parser.add_argument(
        '--network',
        default='default',
        help="""\
        The network to which this rule is attached. If omitted, the
        rule is attached to the ``default'' network.
        """)

  ruleset_parser = parser
  if with_egress_support:
    ruleset_parser = parser.add_mutually_exclusive_group(
        required=not for_update)
  ruleset_parser.add_argument(
      '--allow',
      metavar=ALLOWED_METAVAR,
      type=arg_parsers.ArgList(min_length=min_length),
      required=(not for_update) and (not with_egress_support),
      help="""\
      A list of protocols and ports whose traffic will be allowed.

      The protocols allowed over this connection. This can be the
      (case-sensitive) string values `tcp`, `udp`, `icmp`, `esp`, `ah`, `sctp`,
      or any IP protocol number. An IP-based protocol must be specified for each
      rule. The rule applies only to specified protocol.

      For port-based protocols - `tcp`, `udp`, and `sctp` - a list of
      destination ports or port ranges to which the rule applies may optionally
      be specified. If no port or port range is specified, the rule applies to
      all destination ports.

      The ICMP protocol is supported, but there is no support for configuring
      ICMP packet filtering by ICMP code.

      For example, to create a rule that allows TCP traffic through port 80 and
      ICMP traffic:

        $ {command} MY-RULE --allow tcp:80,icmp

      To create a rule that allows TCP traffic from port 20000 to 25000:

        $ {command} MY-RULE --allow tcp:20000-25000

      To create a rule that allows all TCP traffic:

        $ {command} MY-RULE --allow tcp

      """ + ("""
      Setting this will override the current values.
      """ if for_update else ''))

  parser.add_argument(
      '--description',
      help='A textual description for the firewall rule.{0}'.format(
          ' Set to an empty string to clear existing.' if for_update else ''))

  source_ranges_help = """\
      A list of IP address blocks that are allowed to make inbound
      connections that match the firewall rule to the instances on
      the network. The IP address blocks must be specified in CIDR
      format:
      link:http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing[].

      If neither --source-ranges nor --source-tags are specified,
      --source-ranges defaults to `0.0.0.0/0`, which means that the rule applies
      to all incoming IPv4 connections from inside or outside the network. If
      both --source-ranges and --source-tags are specified, the rule matches if
      either the range of the source matches  --source-ranges or the tag of the
      source matches --source-tags.
      """
  if for_update:
    source_ranges_help += """
      Setting this will override the existing source ranges for the firewall.
      The following will clear the existing source ranges:

        $ {command} MY-RULE --source-ranges
      """
  else:
    source_ranges_help += """
      Multiple IP address blocks can be specified if they are separated by
      commas.
      """
  parser.add_argument(
      '--source-ranges',
      default=None if for_update else [],
      metavar='CIDR_RANGE',
      type=arg_parsers.ArgList(min_length=min_length),
      help=source_ranges_help)

  source_tags_help = """\
      A list of instance tags indicating the set of instances on the network to
      which the rule applies if all other fields match.  If neither
      --source-ranges nor --source-tags are specified, --source-ranges
      defaults to `0.0.0.0/0`, which means that the rule applies to all
      incoming IPv4 connections from inside or outside the network.

      If both --source-ranges and --source-tags are specified, an inbound
      connection is allowed if either the range of the source matches
      --source-ranges or the tag of the source matches --source-tags.

      Tags can be assigned to instances during instance creation.
      """
  if with_service_account:
    source_tags_help += """
      If source tags are specified then neither a source nor target service
      account can also be specified.
      """
  if for_update:
    source_tags_help += """
      Setting this will override the existing source tags for the firewall.
      The following will clear the existing source tags:

        $ {command} MY-RULE --source-tags
      """
  parser.add_argument(
      '--source-tags',
      default=None if for_update else [],
      metavar='TAG',
      type=arg_parsers.ArgList(min_length=min_length),
      help=source_tags_help)

  target_tags_help = """\
      A list of instance tags indicating which instances the rule is applied to.
      If the field is set, the rule applies to only instances with a matching
      tag. If omitted, the rule applies to all instances in the network.

      Tags can be assigned to instances during instance creation.
      """
  if with_service_account:
    target_tags_help = """\

      List of instance tags indicating the set of instances on the
      network which may accept connections that match the
      firewall rule.
      Note that tags can be assigned to instances during instance creation.

      If target tags are specified, then neither a source nor target
      service account can also be specified.

      If both target tags and target service account
      are omitted, all instances on the network can receive
      connections that match the rule.
      """
  if for_update:
    target_tags_help += """
      Setting this will override the existing target tags for the firewall.
      The following will clear the existing target tags:

        $ {command} MY-RULE --target-tags
      """
  parser.add_argument(
      '--target-tags',
      default=None if for_update else [],
      metavar='TAG',
      type=arg_parsers.ArgList(min_length=min_length),
      help=target_tags_help)

  disabled_help = """\
      Disable a firewall rule and stop it from being enforced in the network.
      If a firewall rule is disabled, the associated network behaves as if the
      rule did not exist. To enable a disabled rule, use:

       $ {parent_command} update MY-RULE --no-disabled

      """
  if not for_update:
    disabled_help += """Firewall rules are enabled by default."""
  parser.add_argument(
      '--disabled', action='store_true', default=None, help=disabled_help)

  # Add egress deny firewall cli support.
  if with_egress_support:
    AddArgsForEgress(parser, ruleset_parser, for_update)


def AddArgsForEgress(parser, ruleset_parser, for_update=False):
  """Adds arguments for egress firewall create or update subcommands."""
  min_length = 0 if for_update else 1

  if not for_update:
    ruleset_parser.add_argument(
        '--action',
        choices=['ALLOW', 'DENY'],
        type=lambda x: x.upper(),
        help="""\
        The action for the firewall rule: whether to allow or deny matching
        traffic. If specified, the flag `--rules` must also be specified.
        """)

  rules_help = """\
      A list of protocols and ports to which the firewall rule will apply.

      PROTOCOL is the IP protocol whose traffic will be checked.
      PROTOCOL can be either the name of a well-known protocol
      (e.g., tcp or icmp) or the IP protocol number.
      A list of IP protocols can be found at
      http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml

      A port or port range can be specified after PROTOCOL to which the
      firewall rule apply on traffic through specific ports. If no port
      or port range is specified, connections through all ranges are applied.
      TCP and UDP rules must include a port or port range.
      """
  if for_update:
    rules_help += """
      Setting this will override the current values.
      """
  else:
    rules_help += """
      If specified, the flag --action must also be specified.

      For example, the following will create a rule that blocks TCP
      traffic through port 80 and ICMP traffic:

        $ {command} MY-RULE --action deny --rules tcp:80,icmp
      """
  parser.add_argument(
      '--rules',
      metavar=ALLOWED_METAVAR,
      type=arg_parsers.ArgList(min_length=min_length),
      help=rules_help,
      required=False)

  # Do NOT allow change direction in update case.
  if not for_update:
    parser.add_argument(
        '--direction',
        choices=['INGRESS', 'EGRESS', 'IN', 'OUT'],
        type=lambda x: x.upper(),
        help="""\
        If direction is NOT specified, then default is to apply on incoming
        traffic. For outbound traffic, it is NOT supported to specify
        source-tags.

        For convenience, 'IN' can be used to represent ingress direction and
        'OUT' can be used to represent egress direction.
        """)

  parser.add_argument(
      '--priority',
      type=int,
      help="""\
      This is an integer between 0 and 65535, both inclusive. When NOT
      specified, the value assumed is 1000. Relative priority determines
      precedence of conflicting rules: lower priority values imply higher
      precedence. DENY rules take precedence over ALLOW rules having equal
      priority.
      """)

  destination_ranges_help = """\
      The firewall rule will apply to traffic that has destination IP address
      in these IP address block list. The IP address blocks must be specified
      in CIDR format:
      link:http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing[].
      """
  if for_update:
    destination_ranges_help += """
      Setting this will override the existing destination ranges for the
      firewall. The following will clear the existing destination ranges:

        $ {command} MY-RULE --destination-ranges
      """
  else:
    destination_ranges_help += """
      If --destination-ranges is NOT provided, then this
      flag will default to 0.0.0.0/0, allowing all IPv4 destinations. Multiple
      IP address blocks can be specified if they are separated by commas.
      """
  parser.add_argument(
      '--destination-ranges',
      default=None if for_update else [],
      metavar='CIDR_RANGE',
      type=arg_parsers.ArgList(min_length=min_length),
      help=destination_ranges_help)


def AddArgsForServiceAccount(parser, for_update=False):
  """Adds arguments for secure firewall create or update subcommands."""
  min_length = 0 if for_update else 1
  source_service_accounts_help = """\
      The email of a service account indicating the set of instances on the
      network which match a traffic source in the firewall rule.

      If a source service account is specified then neither source tags nor
      target tags can also be specified.
      """
  if for_update:
    source_service_accounts_help += """
      Setting this will override the existing source service accounts for the
      firewall.
      The following will clear the existing source service accounts:

        $ {command} MY-RULE --source-service-accounts
      """
  parser.add_argument(
      '--source-service-accounts',
      default=None if for_update else [],
      metavar='EMAIL',
      type=arg_parsers.ArgList(min_length=min_length),
      help=source_service_accounts_help)

  target_service_accounts_help = """\
      The email of a service account indicating the set of instances to which
      firewall rules apply. If both target tags and target service account are
      omitted,  the firewall rule is applied to all instances on the network.

      If a target service account is specified then neither source tag nor
      target tags can also be specified.
      """
  if for_update:
    target_service_accounts_help += """
      Setting this will override the existing target service accounts for the
      firewall.
      The following will clear the existing target service accounts:

        $ {command} MY-RULE --target-service-accounts
      """
  parser.add_argument(
      '--target-service-accounts',
      default=None if for_update else [],
      metavar='EMAIL',
      type=arg_parsers.ArgList(min_length=min_length),
      help=target_service_accounts_help)


def ParseRules(rules, message_classes, action=ActionType.ALLOW):
  """Parses protocol:port mappings from --allow or --rules command line."""
  rule_value_list = []
  for spec in rules or []:
    match = LEGAL_SPECS.match(spec)
    if not match:
      raise compute_exceptions.ArgumentError(
          'Firewall rules must be of the form {0}; received [{1}].'.format(
              ALLOWED_METAVAR, spec))
    if match.group('ports'):
      ports = [match.group('ports')]
    else:
      ports = []

    if action == ActionType.ALLOW:
      rule = message_classes.Firewall.AllowedValueListEntry(
          IPProtocol=match.group('protocol'), ports=ports)
    else:
      rule = message_classes.Firewall.DeniedValueListEntry(
          IPProtocol=match.group('protocol'), ports=ports)
    rule_value_list.append(rule)
  return rule_value_list


def SortNetworkFirewallRules(client, rules):
  """Sort the network firewall rules by direction and priority."""
  ingress_network_firewall = [
      item for item in rules if item.direction ==
      client.messages.Firewall.DirectionValueValuesEnum.INGRESS
  ]
  ingress_network_firewall.sort(key=lambda x: x.priority, reverse=False)
  egress_network_firewall = [
      item for item in rules if item.direction ==
      client.messages.Firewall.DirectionValueValuesEnum.EGRESS
  ]
  egress_network_firewall.sort(key=lambda x: x.priority, reverse=False)
  return ingress_network_firewall + egress_network_firewall


def SortOrgFirewallRules(client, rules):
  """Sort the organization firewall rules by direction and priority."""
  ingress_org_firewall_rule = [
      item for item in rules if item.direction ==
      client.messages.SecurityPolicyRule.DirectionValueValuesEnum.INGRESS
  ]
  ingress_org_firewall_rule.sort(key=lambda x: x.priority, reverse=False)
  egress_org_firewall_rule = [
      item for item in rules if item.direction ==
      client.messages.SecurityPolicyRule.DirectionValueValuesEnum.EGRESS
  ]
  egress_org_firewall_rule.sort(key=lambda x: x.priority, reverse=False)
  return ingress_org_firewall_rule + egress_org_firewall_rule


def SortFirewallPolicyRules(client, rules):
  """Sort the organization firewall rules by direction and priority."""
  ingress_org_firewall_rule = [
      item for item in rules if item.direction ==
      client.messages.FirewallPolicyRule.DirectionValueValuesEnum.INGRESS
  ]
  ingress_org_firewall_rule.sort(key=lambda x: x.priority, reverse=False)
  egress_org_firewall_rule = [
      item for item in rules if item.direction ==
      client.messages.FirewallPolicyRule.DirectionValueValuesEnum.EGRESS
  ]
  egress_org_firewall_rule.sort(key=lambda x: x.priority, reverse=False)
  return ingress_org_firewall_rule + egress_org_firewall_rule


def ConvertFirewallPolicyRulesToEffectiveFwRules(
    client,
    firewall_policy,
    support_network_firewall_policy,
    support_region_network_firewall_policy=True):
  """Convert organization firewall policy rules to effective firewall rules."""
  result = []
  for rule in firewall_policy.rules:
    item = {}
    if (firewall_policy.type == client.messages
        .NetworksGetEffectiveFirewallsResponseEffectiveFirewallPolicy
        .TypeValueValuesEnum.HIERARCHY or firewall_policy.type == client
        .messages.InstancesGetEffectiveFirewallsResponseEffectiveFirewallPolicy
        .TypeValueValuesEnum.HIERARCHY or
        (support_region_network_firewall_policy and
         firewall_policy.type == client.messages.
         RegionNetworkFirewallPoliciesGetEffectiveFirewallsResponseEffectiveFirewallPolicy
         .TypeValueValuesEnum.HIERARCHY)):
      item.update({'type': 'org-firewall'})
    elif support_network_firewall_policy and (
        firewall_policy.type == client.messages
        .NetworksGetEffectiveFirewallsResponseEffectiveFirewallPolicy
        .TypeValueValuesEnum.NETWORK or firewall_policy.type == client.messages
        .InstancesGetEffectiveFirewallsResponseEffectiveFirewallPolicy
        .TypeValueValuesEnum.NETWORK or
        (support_region_network_firewall_policy and
         firewall_policy.type == client.messages.
         RegionNetworkFirewallPoliciesGetEffectiveFirewallsResponseEffectiveFirewallPolicy
         .TypeValueValuesEnum.NETWORK)):
      item.update({'type': 'network-firewall-policy'})
    elif support_network_firewall_policy and (
        firewall_policy.type == client.messages
        .InstancesGetEffectiveFirewallsResponseEffectiveFirewallPolicy
        .TypeValueValuesEnum.NETWORK_REGIONAL or
        (support_region_network_firewall_policy and
         firewall_policy.type == client.messages.
         RegionNetworkFirewallPoliciesGetEffectiveFirewallsResponseEffectiveFirewallPolicy
         .TypeValueValuesEnum.NETWORK_REGIONAL)):
      item.update({'type': 'network-regional-firewall-policy'})
    else:
      item.update({'type': 'unknown'})
    item.update({'description': rule.description})
    item.update({'firewall_policy_name': firewall_policy.name})
    item.update({'priority': rule.priority})
    item.update({'direction': rule.direction})
    item.update({'action': rule.action.upper()})
    item.update({'disabled': bool(rule.disabled)})
    if rule.match.srcIpRanges:
      item.update({'ip_ranges': rule.match.srcIpRanges})
    if rule.match.destIpRanges:
      item.update({'ip_ranges': rule.match.destIpRanges})
    if rule.targetServiceAccounts:
      item.update({'target_svc_acct': rule.targetServiceAccounts})
    if rule.targetResources:
      item.update({'target_resources': rule.targetResources})
    result.append(item)
  return result


def ConvertOrgSecurityPolicyRulesToEffectiveFwRules(security_policy):
  """Convert organization security policy rules to effective firewall rules."""
  result = []
  for rule in security_policy.rules:
    item = {}
    item.update({'type': 'org-firewall'})
    item.update({'description': rule.description})
    item.update({'firewall_policy_name': security_policy.id})
    item.update({'priority': rule.priority})
    item.update({'direction': rule.direction})
    item.update({'action': rule.action.upper()})
    item.update({'disabled': 'False'})
    if rule.match.config.srcIpRanges:
      item.update({'ip_ranges': rule.match.config.srcIpRanges})
    if rule.match.config.destIpRanges:
      item.update({'ip_ranges': rule.match.config.destIpRanges})
    if rule.targetServiceAccounts:
      item.update({'target_svc_acct': rule.targetServiceAccounts})
    if rule.targetResources:
      item.update({'target_resources': rule.targetResources})
    result.append(item)
  return result


def ConvertNetworkFirewallRulesToEffectiveFwRules(network_firewalls):
  """Convert network firewall rules to effective firewall rules."""
  result = []
  for rule in network_firewalls:
    item = {}
    item.update({'type': 'network-firewall'})
    item.update({'description': rule.description})
    item.update({'priority': rule.priority})
    item.update({'direction': rule.direction})
    if rule.allowed:
      item.update({'action': 'ALLOW'})
    else:
      item.update({'action': 'DENY'})
    if rule.sourceRanges:
      item.update({'ip_ranges': rule.sourceRanges})
    if rule.destinationRanges:
      item.update({'ip_ranges': rule.destinationRanges})
    if rule.targetServiceAccounts:
      item.update({'target_svc_acct': rule.targetServiceAccounts})
    if rule.targetTags:
      item.update({'target_tags': rule.targetTags})
    if rule.sourceTags:
      item.update({'src_tags': rule.sourceTags})
    if rule.sourceServiceAccounts:
      item.update({'src_svc_acct': rule.sourceTags})
    if rule.disabled:
      item.update({'disabled': True})
    else:
      item.update({'disabled': False})
    item.update({'name': rule.name})
    result.append(item)
  return result
