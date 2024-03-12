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
"""Flags and helpers for the compute ssl-policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

# The default output format for the list sub-command.
DEFAULT_LIST_FORMAT = """\
    table(
      name,
      profile,
      minTlsVersion
    )"""

# The default output format for the list sub-command.
DEFAULT_AGGREGATED_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      profile,
      minTlsVersion
    )"""

# Mapping between user supplied argument to the string expected by API.
_TLS_VERSION_MAP = {
    '1.0': 'TLS_1_0',
    '1.1': 'TLS_1_1',
    '1.2': 'TLS_1_2',
}


class GlobalSslPoliciesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalSslPoliciesCompleter, self).__init__(
        collection='compute.sslPolicies',
        list_command='compute ssl-policies list --global --uri',
        **kwargs)


class RegionalSslPoliciesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalSslPoliciesCompleter, self).__init__(
        collection='compute.regionSslPolicies',
        list_command='compute ssl-policies list --filter=region:* --uri',
        **kwargs)


class SslPoliciesCompleter(compute_completers.ListCommandCompleter):
  """An SSL policy completer for a resource argument."""

  def __init__(self, **kwargs):
    super(SslPoliciesCompleter, self).__init__(
        completers=[GlobalSslPoliciesCompleter, RegionalSslPoliciesCompleter],
        **kwargs)


def GetSslPolicyArgument(required=True, plural=False):
  """Returns the resource argument object for the SSL policy flag."""
  return compute_flags.ResourceArgument(
      name='SSL_POLICY',
      resource_name='SSL policy',
      completer=SslPoliciesCompleter,
      plural=plural,
      custom_plural='SSL policies',
      required=required,
      global_collection='compute.sslPolicies')


def GetSslPolicyArgumentForOtherResource(proxy_type, required=False):
  """Returns the flag for specifying the SSL policy."""
  return compute_flags.ResourceArgument(
      name='--ssl-policy',
      resource_name='SSL policy',
      completer=SslPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.sslPolicies',
      short_help=(
          'A reference to an SSL policy resource that defines the server-side '
          'support for SSL features.'),
      detailed_help="""\
        A reference to an SSL policy resource that defines the server-side
        support for SSL features and affects the connections between clients
        and load balancers that are using the {proxy_type} proxy. The SSL
        policy must exist and cannot be
        deleted while referenced by a target {proxy_type} proxy.
        """.format(proxy_type=proxy_type))


def GetSslPolicyMultiScopeArgument(required=True, plural=False):
  """Returns the resource argument object for the SSL policy flag."""
  return compute_flags.ResourceArgument(
      name='SSL_POLICY',
      resource_name='SSL policy',
      completer=SslPoliciesCompleter,
      plural=plural,
      custom_plural='SSL policies',
      required=required,
      regional_collection='compute.regionSslPolicies',
      global_collection='compute.sslPolicies')


def GetSslPolicyMultiScopeArgumentForOtherResource(proxy_type, required=False):
  """Returns the flag for specifying the SSL policy."""
  return compute_flags.ResourceArgument(
      name='--ssl-policy',
      resource_name='SSL policy',
      completer=SslPoliciesCompleter,
      plural=False,
      required=required,
      regional_collection='compute.regionSslPolicies',
      global_collection='compute.sslPolicies',
      short_help=(
          'A reference to an SSL policy resource that defines the server-side '
          'support for SSL features.'),
      detailed_help="""\
        A reference to an SSL policy resource that defines the server-side
        support for SSL features and affects the connections between clients
        and load balancers that are using the {proxy_type} proxy. The SSL
        policy must exist and cannot be
        deleted while referenced by a target {proxy_type} proxy.
        """.format(proxy_type=proxy_type))


def GetClearSslPolicyArgumentForOtherResource(proxy_type, required=False):
  """Returns the flag for clearing the SSL policy."""
  return base.Argument(
      '--clear-ssl-policy',
      action='store_true',
      default=False,
      required=required,
      help="""\
      Removes any attached SSL policy from the {} proxy.
      """.format(proxy_type))


def GetDescriptionFlag():
  """Returns the flag for SSL policy description."""
  return base.Argument(
      '--description',
      help='An optional, textual description for the SSL policy.')


def GetProfileFlag(default=None):
  """Returns the flag for specifying the SSL policy profile."""
  return base.Argument(
      '--profile',
      choices={
          'COMPATIBLE': (
              'Compatible profile. Allows the broadest set of clients, even '
              'those which support only out-of-date SSL features, to negotiate '
              'SSL with the load balancer.'),
          'MODERN':
              ('Modern profile. Supports a wide set of SSL features, allowing '
               'modern clients to negotiate SSL.'),
          'RESTRICTED':
              ('Restricted profile. Supports a reduced set of SSL features, '
               'intended to meet stricter compliance requirements.'),
          'CUSTOM': (
              'Custom profile. Allows customization by selecting only the '
              'features which are required. The list of all available features '
              'can be obtained using:\n\n'
              '  gcloud compute ssl-policies list-available-features\n'),
      },
      default=default,
      help=(
          'SSL policy profile. Changing profile from CUSTOM to '
          'COMPATIBLE|MODERN|RESTRICTED will clear the custom-features field.'))


def GetMinTlsVersionFlag(default=None):
  """Returns the flag for specifying minimum TLS version of an SSL policy."""
  return base.Argument(
      '--min-tls-version',
      choices={
          '1.0': 'TLS 1.0.',
          '1.1': 'TLS 1.1.',
          '1.2': 'TLS 1.2.',
      },
      default=default,
      help='Minimum TLS version.')


def GetCustomFeaturesFlag():
  """Returns the flag for specifying custom features in an SSL policy."""
  return base.Argument(
      '--custom-features',
      metavar='CUSTOM_FEATURES',
      type=arg_parsers.ArgList(),
      help=(
          'A comma-separated list of custom features, required when the '
          'profile being used is CUSTOM.\n\n'
          'Using CUSTOM profile allows customization of the features that are '
          'part of the SSL policy. This flag allows specifying those custom '
          'features.\n\n'
          'The list of all supported custom features can be obtained using:\n\n'
          '  gcloud compute ssl-policies list-available-features\n'))


def ParseTlsVersion(tls_version):
  return _TLS_VERSION_MAP[tls_version] if tls_version else None
