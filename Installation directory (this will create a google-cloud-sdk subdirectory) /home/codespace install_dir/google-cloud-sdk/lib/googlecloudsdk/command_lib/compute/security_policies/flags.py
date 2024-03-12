# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute security policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util import completers


class GlobalSecurityPoliciesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalSecurityPoliciesCompleter, self).__init__(
        collection='compute.securityPolicies',
        list_command='compute security-policies list --uri',
        **kwargs)


class RegionalSecurityPoliciesCompleter(compute_completers.ListCommandCompleter
                                       ):

  def __init__(self, **kwargs):
    super(RegionalSecurityPoliciesCompleter, self).__init__(
        collection='compute.regionSecurityPolicies',
        list_command=('compute security-policies list '
                      '--filter=region:* --uri'),
        **kwargs)


class SecurityPoliciesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(SecurityPoliciesCompleter, self).__init__(
        completers=[
            GlobalSecurityPoliciesCompleter, RegionalSecurityPoliciesCompleter
        ],
        **kwargs)


def SecurityPolicyArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      completer=SecurityPoliciesCompleter,
      plural=plural,
      custom_plural='security policies',
      required=required,
      global_collection='compute.securityPolicies')


def SecurityPolicyRegionalArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      completer=SecurityPoliciesCompleter,
      plural=plural,
      custom_plural='security policies',
      required=required,
      regional_collection='compute.regionSecurityPolicies')


def SecurityPolicyMultiScopeArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      completer=SecurityPoliciesCompleter,
      plural=plural,
      custom_plural='security policies',
      required=required,
      global_collection='compute.securityPolicies',
      regional_collection='compute.regionSecurityPolicies')


def SecurityPolicyArgumentForTargetResource(resource, required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      short_help=('The security policy that will be set for this {0}.'.format(
          resource)))


def SecurityPolicyRegionalArgumentForTargetResource(resource, required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=RegionalSecurityPoliciesCompleter,
      plural=False,
      required=required,
      regional_collection='compute.regionSecurityPolicies',
      short_help=(
          ('The security policy that will be set for this {0}. To remove the '
           'policy from this {0} set the policy to an empty string.'
          ).format(resource)))


def SecurityPolicyMultiScopeArgumentForTargetResource(
    resource,
    required=False,
    region_hidden=False,
    scope_flags_usage=compute_flags.ScopeFlagsUsage
    .GENERATE_DEDICATED_SCOPE_FLAGS,
    short_help_text=None):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      regional_collection='compute.regionSecurityPolicies',
      region_hidden=region_hidden,
      short_help=(
          (short_help_text or
           'The security policy that will be set for this {0}. To remove the '
           'policy from this {0} set the policy to an empty string.'
          ).format(resource)),
      scope_flags_usage=scope_flags_usage)


def EdgeSecurityPolicyArgumentForTargetResource(resource, required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--edge-security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      short_help=(
          ('The edge security policy that will be set for this {0}. To remove '
           'the policy from this {0} set the policy to an empty string.'
          ).format(resource)))


def SecurityPolicyArgumentForRules(required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      short_help='The security policy that this rule belongs to.')


def SecurityPolicyMultiScopeArgumentForRules(required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      regional_collection='compute.regionSecurityPolicies',
      region_hidden=True,
      scope_flags_usage=compute_flags.ScopeFlagsUsage.USE_EXISTING_SCOPE_FLAGS,
      short_help='The security policy that this rule belongs to.')


def AddCloudArmorAdaptiveProtection(parser, required=False):
  """Adds the cloud armor adaptive protection arguments to the argparse."""
  parser.add_argument(
      '--enable-layer7-ddos-defense',
      action='store_true',
      default=None,
      required=required,
      help=('Whether to enable Cloud Armor Layer 7 DDoS Defense Adaptive '
            'Protection.'))
  parser.add_argument(
      '--layer7-ddos-defense-rule-visibility',
      choices=['STANDARD', 'PREMIUM'],
      type=lambda x: x.upper(),
      required=required,
      metavar='VISIBILITY_TYPE',
      help=('The visibility type indicates whether the rules are opaque or '
            'transparent.'))


def AddCloudArmorAdaptiveProtectionAutoDeploy(parser):
  """Adds the cloud armor adaptive protection's auto-deploy arguments to the argparse."""
  parser.add_argument(
      '--layer7-ddos-defense-auto-deploy-load-threshold',
      type=float,
      help=(
          "Load threshold above which Adaptive Protection's auto-deploy takes actions"
      ))
  parser.add_argument(
      '--layer7-ddos-defense-auto-deploy-confidence-threshold',
      type=float,
      help=(
          "Confidence threshold above which Adaptive Protection's auto-deploy takes actions"
      ))
  parser.add_argument(
      '--layer7-ddos-defense-auto-deploy-impacted-baseline-threshold',
      type=float,
      help=(
          "Impacted baseline threshold below which Adaptive Protection's auto-deploy takes actions"
      ))
  parser.add_argument(
      '--layer7-ddos-defense-auto-deploy-expiration-sec',
      type=int,
      help=(
          "Duration over which Adaptive Protection's auto-deployed actions last"
      ))


def AddAdvancedOptions(parser, required=False):
  """Adds the cloud armor advanced options arguments to the argparse."""
  parser.add_argument(
      '--json-parsing',
      choices=['DISABLED', 'STANDARD', 'STANDARD_WITH_GRAPHQL'],
      type=lambda x: x.upper(),
      required=required,
      help=('The JSON parsing behavior for this rule. '
            'Must be one of the following values: '
            '[DISABLED, STANDARD, STANDARD_WITH_GRAPHQL].'))

  parser.add_argument(
      '--json-custom-content-types',
      type=arg_parsers.ArgList(),
      metavar='CONTENT_TYPE',
      help="""\
      A comma-separated list of custom Content-Type header values to apply JSON
      parsing for preconfigured WAF rules. Only applicable when JSON parsing is
      enabled, like ``--json-parsing=STANDARD''. When configuring a Content-Type
      header value, only the type/subtype needs to be specified, and the
      parameters should be excluded.
      """)

  parser.add_argument(
      '--log-level',
      choices=['NORMAL', 'VERBOSE'],
      type=lambda x: x.upper(),
      required=required,
      help='The level of detail to display for WAF logging.')

  parser.add_argument(
      '--user-ip-request-headers',
      type=arg_parsers.ArgList(),
      metavar='USER_IP_REQUEST_HEADER',
      help="""\
      A comma-separated list of request header names to use for resolving the
      caller's user IP address.
      """)


def AddDdosProtectionConfig(parser, required=False):
  """Adds the cloud armor DDoS protection config arguments to the argparse."""
  parser.add_argument(
      '--network-ddos-protection',
      choices=['STANDARD', 'ADVANCED'],
      type=lambda x: x.upper(),
      required=required,
      help=(
          'The DDoS protection level for network load balancing and instances '
          'with external IPs'
      ),
  )


def AddDdosProtectionConfigWithAdvancedPreview(parser, required=False):
  """Adds the cloud armor DDoS protection config arguments to the argparse."""
  parser.add_argument(
      '--network-ddos-protection',
      choices=['STANDARD', 'ADVANCED', 'ADVANCED_PREVIEW'],
      type=lambda x: x.upper(),
      required=required,
      help=(
          'The DDoS protection level for network load balancing and instances '
          'with external IPs'
      ),
  )


def AddDdosProtectionConfigOld(parser, required=False):
  """Adds the cloud armor DDoS protection config arguments to the argparse."""
  parser.add_argument(
      '--ddos-protection',
      choices=['STANDARD', 'ADVANCED', 'ADVANCED_PREVIEW'],
      type=lambda x: x.upper(),
      required=required,
      help=(
          'The DDoS protection level for network load balancing and instances '
          'with external IPs'
      ),
  )


def AddRecaptchaOptions(parser, required=False):
  """Adds the cloud armor reCAPTCHA options arguments to the argparse."""
  parser.add_argument(
      '--recaptcha-redirect-site-key',
      required=required,
      help="""\
      The reCAPTCHA site key to be used for rules using the ``redirect'' action
      and the ``google-recaptcha'' redirect type under the security policy.
      """)
