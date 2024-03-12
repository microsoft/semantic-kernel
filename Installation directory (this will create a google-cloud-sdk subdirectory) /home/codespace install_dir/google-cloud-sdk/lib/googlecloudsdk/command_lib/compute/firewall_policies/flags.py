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
"""Flags and helpers for the compute organization firewall policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

# TODO(b/175792396): change displayName to shortName once API is rolled out
DEFAULT_LIST_FORMAT = """\
    table(
      name:label=ID,
      displayName,
      description
    )"""


class FirewallPoliciesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(FirewallPoliciesCompleter, self).__init__(
        collection='compute.firewallPolicies',
        list_command='compute org-firewall-policies list --uri',
        **kwargs)


def FirewallPolicyRuleListArgument(required=False,
                                   plural=False,
                                   operation=None):
  return compute_flags.ResourceArgument(
      name='FIREWALL_POLICY',
      resource_name='firewall policy',
      completer=FirewallPoliciesCompleter,
      plural=plural,
      required=required,
      custom_plural='firewall policies',
      short_help='Short name of the firewall policy to {0}.'.format(operation),
      global_collection='compute.firewallPolicies')


def FirewallPolicyArgument(required=False, plural=False, operation=None):
  return compute_flags.ResourceArgument(
      name='FIREWALL_POLICY',
      resource_name='firewall policy',
      completer=FirewallPoliciesCompleter,
      plural=plural,
      required=required,
      custom_plural='firewall policies',
      short_help='Short name or ID of the firewall policy to {0}.'.format(
          operation),
      global_collection='compute.firewallPolicies')


def FirewallPolicyAssociationsArgument(required=False, plural=False):
  return compute_flags.ResourceArgument(
      name='name',
      resource_name='association',
      completer=FirewallPoliciesCompleter,
      plural=plural,
      required=required,
      global_collection='compute.firewallPolicies')


def FirewallPolicyRuleArgument(
    required=False,
    plural=False,
    operation=None,
):
  return compute_flags.ResourceArgument(
      name='priority',
      resource_name='firewall policy rule',
      completer=FirewallPoliciesCompleter,
      plural=plural,
      required=required,
      global_collection='compute.firewallPolicies',
      short_help='Priority of the firewall policy rule to {}.'.format(
          operation))


def AddArgFirewallPolicyCreation(parser):
  """Adds the argument for firewall policy creaton."""
  parser.add_argument(
      '--short-name',
      required=True,
      help=('A textual name of the firewall policy. The name must be 1-63 '
            'characters long, and comply with RFC 1035.'))

  group = parser.add_group(required=True, mutex=True)

  group.add_argument(
      '--organization',
      help=('Organization in which the organization firewall policy'
            ' is to be created.'))

  group.add_argument(
      '--folder',
      help=('Folder in which the organization firewall policy is to be'
            ' created.'))

  parser.add_argument(
      '--description',
      help=('An optional, textual description for the organization security'
            ' policy.'))


def AddArgsCloneRules(parser):
  """Adds the argument for firewall policy clone rules."""
  parser.add_argument(
      '--source-firewall-policy',
      required=True,
      help=('The URL of the source firewall policy to copy the rules from.'))

  parser.add_argument(
      '--organization',
      help=('Organization in which the organization firewall policy to copy the'
            ' rules to. Must be set if firewall-policy is short name.'))


def AddArgsListFirewallPolicy(parser):
  """Adds the argument for firewall policy list."""
  group = parser.add_group(required=True, mutex=True)

  group.add_argument(
      '--organization',
      help=('Organization in which firewall policies are listed'))

  group.add_argument(
      '--folder', help=('Folder in which firewall policies are listed'))


def AddArgsMove(parser):
  """Adds the argument for firewall policy move."""
  parser.add_argument(
      '--organization',
      help=('Organization in which the organization firewall policy is to be'
            ' moved. Must be set if FIREWALL_POLICY is short name.'))

  parser.add_argument(
      '--folder',
      help=('Folder to which the organization firewall policy is to be'
            ' moved.'))


def AddArgsUpdateFirewallPolicy(parser):
  """Adds the argument for firewall policy update."""
  parser.add_argument(
      '--organization',
      help=('Organization in which the organization firewall policy is to be'
            ' updated. Must be set if FIREWALL_POLICY is short name.'))
  parser.add_argument(
      '--description',
      help=('An optional, textual description for the organization security'
            ' policy.'))


def AddPriority(parser, operation, is_plural=False):
  """Adds the priority argument to the argparse."""
  parser.add_argument(
      'name' + ('s' if is_plural else ''),
      metavar='PRIORITY',
      nargs='*' if is_plural else None,
      completer=FirewallPoliciesCompleter,
      help=('Priority of the rule{0} to {1}. Rules are evaluated in order '
            'from highest priority to lowest priority where 0 is the highest '
            'priority and 2147483647 is the lowest priority.'.format(
                's' if is_plural else '', operation)))


def AddAction(parser, required=True):
  """Adds the action argument to the argparse."""
  parser.add_argument(
      '--action',
      choices=['allow', 'deny', 'goto_next', 'apply_security_profile_group'],
      type=lambda x: x.lower(),
      required=required,
      help='Action to take if the request matches the match condition.',
  )


def AddFirewallPolicyId(parser, required=True, operation=None):
  """Adds the firewall policy ID argument to the argparse."""
  parser.add_argument(
      '--firewall-policy',
      required=required,
      help=('Short name of the firewall policy into which the rule should '
            'be {}.'.format(operation)))


def AddOrganization(parser, required=True):
  parser.add_argument(
      '--organization',
      required=required,
      help=('Organization which the organization firewall policy belongs to. '
            'Must be set if FIREWALL_POLICY is short name.'))


def AddSrcIpRanges(parser, required=False):
  """Adds the source IP ranges."""
  parser.add_argument(
      '--src-ip-ranges',
      type=arg_parsers.ArgList(),
      required=required,
      metavar='SRC_IP_RANGE',
      help='Source IP ranges to match for this rule.')


def AddDestIpRanges(parser, required=False):
  """Adds the destination IP ranges."""
  parser.add_argument(
      '--dest-ip-ranges',
      type=arg_parsers.ArgList(),
      required=required,
      metavar='DEST_IP_RANGE',
      help='Destination IP ranges to match for this rule.')


def AddLayer4Configs(parser, required=False):
  """Adds the layer4 configs."""
  parser.add_argument(
      '--layer4-configs',
      type=arg_parsers.ArgList(),
      required=required,
      metavar='LAYER4_CONFIG',
      help=('A list of destination protocols and ports to which the firewall '
            'rule will apply.'))


def AddDirection(parser, required=False):
  """Adds the direction of the traffic to which the rule is applied."""
  parser.add_argument(
      '--direction',
      required=required,
      choices=['INGRESS', 'EGRESS'],
      help=(
          'Direction of the traffic the rule is applied. The default is to apply on incoming traffic.'
      ))


def AddEnableLogging(parser, required=False):
  """Adds the option to enable logging."""
  parser.add_argument(
      '--enable-logging',
      required=required,
      action=arg_parsers.StoreTrueFalseAction,
      help=('Use this flag to enable logging of connections that allowed or '
            'denied by this rule.'))


def AddDisabled(parser, required=False):
  """Adds the option to disable the rule."""
  parser.add_argument(
      '--disabled',
      required=required,
      action=arg_parsers.StoreTrueFalseAction,
      help=('Use this flag to disable the rule. Disabled rules will not affect '
            'traffic.'))


def AddNewPriority(parser, operation=None):
  """Adds the new firewall policy rule priority to the argparse."""
  parser.add_argument(
      '--new-priority',
      help=('New priority for the rule to {}. Valid in [0, 65535]. '.format(
          operation)))


def AddTargetResources(parser, required=False):
  """Adds the target resources the rule is applied to."""
  parser.add_argument(
      '--target-resources',
      type=arg_parsers.ArgList(),
      metavar='TARGET_RESOURCES',
      required=required,
      help=('List of URLs of target resources to which the rule is applied.'))


def AddTargetServiceAccounts(parser, required=False):
  """Adds the target service accounts for the rule."""
  parser.add_argument(
      '--target-service-accounts',
      type=arg_parsers.ArgList(),
      metavar='TARGET_SERVICE_ACCOUNTS',
      required=required,
      help=('List of target service accounts for the rule.'))


def AddDescription(parser, required=False):
  """Adds the description of this rule."""
  parser.add_argument(
      '--description',
      required=required,
      help=('An optional, textual description for the rule.'))


def AddArgsCreateAssociation(parser):
  """Adds the arguments of association creation."""
  parser.add_argument(
      '--firewall-policy',
      required=True,
      help=('Security policy ID of the association.'))
  parser.add_argument(
      '--organization',
      help=('ID of the organization in which the firewall policy is to be'
            ' associated. Must be set if FIREWALL_POLICY is short name.'))

  parser.add_argument(
      '--folder',
      help=('ID of the folder with which the association is created.'))

  parser.add_argument(
      '--replace-association-on-target',
      action='store_true',
      default=False,
      required=False,
      help=(
          'By default, if you attempt to insert an association to an '
          'organization or folder resource that is already associated with a '
          'firewall policy the method will fail. If this is set, the existing '
          ' association will be deleted at the same time that the new '
          'association is created.'))

  parser.add_argument(
      '--name',
      help=('Name to identify this association. If unspecified, the '
            'name will be set to "organization-{ORGANIZATION_ID}" '
            'or "folder-{FOLDER_ID}".'))


def AddArgsDeleteAssociation(parser):
  """Adds the arguments of association deletion."""
  parser.add_argument(
      '--firewall-policy',
      required=True,
      help=('Short name or ID of the firewall policy ID of the association.'))

  parser.add_argument(
      '--organization',
      help=('ID of the organization in which the firewall policy is to be'
            ' detached. Must be set if FIREWALL_POLICY is short name.'))


def AddArgsListAssociation(parser):
  """Adds the arguments of association list."""
  group = parser.add_group(required=True, mutex=True)

  group.add_argument(
      '--organization',
      help=('ID of the organization with which the association is listed.'))

  group.add_argument(
      '--folder',
      help=('ID of the folder with which the association is listed.'))


def AddSrcAddressGroups(parser):
  """Adds a source address group to this rule."""
  parser.add_argument(
      '--src-address-groups',
      type=arg_parsers.ArgList(),
      metavar='SOURCE_ADDRESS_GROUPS',
      required=False,
      help=('Source address groups to match for this rule. '
            'Can only be specified if DIRECTION is ingress.'))


def AddDestAddressGroups(parser):
  """Adds a destination address group to this rule."""
  parser.add_argument(
      '--dest-address-groups',
      type=arg_parsers.ArgList(),
      metavar='DEST_ADDRESS_GROUPS',
      required=False,
      help=(
          'Destination address groups to match for this rule. '
          'Can only be specified if DIRECTION is egress.'
      ),
  )


def AddSrcFqdns(parser):
  """Adds source fqdns to this rule."""
  parser.add_argument(
      '--src-fqdns',
      type=arg_parsers.ArgList(),
      metavar='SOURCE_FQDNS',
      required=False,
      help=(
          'Source FQDNs to match for this rule. '
          'Can only be specified if DIRECTION is `ingress`.'
      ))


def AddDestFqdns(parser):
  """Adds destination fqdns to this rule."""
  parser.add_argument(
      '--dest-fqdns',
      type=arg_parsers.ArgList(),
      metavar='DEST_FQDNS',
      required=False,
      help=(
          'Destination FQDNs to match for this rule. '
          'Can only be specified if DIRECTION is `egress`.'
      ),
  )


def AddSrcRegionCodes(parser):
  """Adds a source region code to this rule."""
  parser.add_argument(
      '--src-region-codes',
      type=arg_parsers.ArgList(),
      metavar='SOURCE_REGION_CODES',
      required=False,
      help=(
          'Source Region Code to match for this rule. '
          'Can only be specified if DIRECTION is `ingress`.'
      ))


def AddDestRegionCodes(parser):
  """Adds a destination region code to this rule."""
  parser.add_argument(
      '--dest-region-codes',
      type=arg_parsers.ArgList(),
      metavar='DEST_REGION_CODES',
      required=False,
      help=(
          'Destination Region Code to match for this rule. '
          'Can only be specified if DIRECTION is `egress`.'
      ),
  )


def AddSrcThreatIntelligence(parser):
  """Adds source threat intelligence list names to this rule."""
  parser.add_argument(
      '--src-threat-intelligence',
      type=arg_parsers.ArgList(),
      metavar='SOURCE_THREAT_INTELLIGENCE_LISTS',
      required=False,
      help=(
          'Source Threat Intelligence lists to match for this rule. '
          'Can only be specified if DIRECTION is `ingress`. '
          'The available lists can be found here: '
          'https://cloud.google.com/vpc/docs/firewall-policies-rule-details#threat-intelligence-fw-policy.'
      ),
  )


def AddDestThreatIntelligence(parser):
  """Adds destination threat intelligence list names to this rule."""
  parser.add_argument(
      '--dest-threat-intelligence',
      type=arg_parsers.ArgList(),
      metavar='DEST_THREAT_INTELLIGENCE_LISTS',
      required=False,
      help=(
          'Destination Threat Intelligence lists to match for this rule. '
          'Can only be specified if DIRECTION is `egress`. '
          'The available lists can be found here: '
          'https://cloud.google.com/vpc/docs/firewall-policies-rule-details#threat-intelligence-fw-policy.'
      ),
  )


def AddSecurityProfileGroup(parser):
  """Adds security profile group to this rule."""
  parser.add_argument(
      '--security-profile-group',
      metavar='SECURITY_PROFILE_GROUP',
      required=False,
      help=(
          'An org-based security profile group to be used with'
          ' apply_security_profile_group action. Allowed formats are: a)'
          ' http(s)://<namespace>/<api>/organizations/<org_id>/locations/global/securityProfileGroups/<profile>'
          ' b) (//)<namespace>/organizations/<org_id>/locations/global/securityProfileGroups/<profile>'
          ' c) <profile>. In case "c" gCloud CLI will create a reference'
          ' matching format "a", but to make it work'
          ' CLOUDSDK_API_ENDPOINT_OVERRIDES_NETWORKSECURITY property must be'
          ' set. In order to set this property, please run the command gcloud'
          ' config set api_endpoint_overrides/networksecurity'
          ' https://<namespace>/.'
      ),
  )


def AddTlsInspect(parser):
  """Adds the option to turn on TLS decryption on the rule."""
  parser.add_argument(
      '--tls-inspect',
      required=False,
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Use this flag to indicate whether TLS traffic should be inspected '
          'using the TLS inspection policy when the security profile group '
          'is applied. Default: no TLS inspection.'
      ),
  )
