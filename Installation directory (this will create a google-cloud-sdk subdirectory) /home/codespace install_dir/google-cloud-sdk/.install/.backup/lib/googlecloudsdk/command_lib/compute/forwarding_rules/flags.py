# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute forwarding-rules commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags as addresses_flags
from googlecloudsdk.command_lib.util import completers

FORWARDING_RULES_OVERVIEW = """
A forwarding rule directs traffic that matches a destination IP address
(and possibly a TCP or UDP port) to a forwarding target (load balancer,
VPN gateway or VM instance).

Forwarding rules can be either global or regional, specified with the
``--global'' or ``--region=REGION'' flags. For more information about
the scope of a forwarding rule, refer to
https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.

Forwarding rules can be external, internal, internal managed, or
internal self-managed, specified with the
``--load-balancing-scheme=[EXTERNAL|EXTERNAL_MANAGED|INTERNAL|INTERNAL_MANAGED|INTERNAL_SELF_MANAGED]''
flag. External forwarding rules are accessible from the internet, while
internal forwarding rules are only accessible from within their VPC
networks. You can specify a reserved static external or internal IP
address with the ``--address=ADDRESS'' flag for the forwarding rule.
Otherwise, if the flag is unspecified, an ephemeral IP address is
automatically assigned (global IP addresses for global forwarding rules
and regional IP addresses for regional forwarding rules); an internal
forwarding rule is automatically assigned an ephemeral internal IP
address from the subnet specified with the ``--subnet'' flag. You must
provide an IP address for an internal self-managed forwarding rule.

Different types of load balancers work at different layers of the OSI
networking model (http://en.wikipedia.org/wiki/Network_layer). Layer 3/4
targets include target pools, target SSL proxies, target TCP proxies,
and backend services. Layer 7 targets include target HTTP proxies and
target HTTPS proxies. For more information, refer to
https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.
"""

FORWARDING_RULES_OVERVIEW_ALPHA = """\
A forwarding rule directs traffic that matches a destination IP address
(and possibly a TCP or UDP port) to a forwarding target (load balancer,
VPN gateway or VM instance).

Forwarding rules can be either global or regional, specified with the
``--global'' or ``--region=REGION'' flag. For more information about
the scope of a forwarding rule, refer to
https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.

Forwarding rules can be external, external managed, internal, internal managed, or
internal self-managed, specified with the
``--load-balancing-scheme=[EXTERNAL|EXTERNAL_MANAGED|INTERNAL|INTERNAL_MANAGED|INTERNAL_SELF_MANAGED]''
flag. External forwarding rules are accessible from the internet, while
internal forwarding rules are only accessible from within their VPC
networks. You can specify a reserved static external or internal IP
address with the ``--address=ADDRESS'' flag for the forwarding rule.
Otherwise, if the flag is unspecified, an ephemeral IP address is
automatically assigned (global IP addresses for global forwarding rules
and regional IP addresses for regional forwarding rules); an internal
forwarding rule is automatically assigned an ephemeral internal IP
address from the subnet specified with the ``--subnet'' flag. You must
provide an IP address for an internal self-managed forwarding rule.

Different types of load balancers work at different layers of the OSI
networking model (http://en.wikipedia.org/wiki/Network_layer). Layer 3
targets include target pools, target SSL proxies, target TCP proxies,
and backend services. Layer 7 targets include target HTTP proxies,
target HTTPS and target gRPC proxies. For more information, refer to
https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.
"""

# This is the list of valid values for the --target-bundle option, used
# for Private Service Connect for Google APIs.
PSC_GOOGLE_APIS_BUNDLES = ['all-apis', 'vpc-sc']


class ForwardingRulesZonalCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesZonalCompleter, self).__init__(
        collection='compute.forwardingRules',
        list_command=('compute forwarding-rules list --filter=region:* --uri'),
        **kwargs)


class ForwardingRulesGlobalCompleter(
    compute_completers.GlobalListCommandCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesGlobalCompleter, self).__init__(
        collection='compute.globalForwardingRules',
        list_command='compute forwarding-rules list --global --uri',
        **kwargs)


class ForwardingRulesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesCompleter, self).__init__(
        completers=[
            ForwardingRulesGlobalCompleter, ForwardingRulesZonalCompleter
        ],
        **kwargs)


def ForwardingRuleArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      completer=ForwardingRulesCompleter,
      required=required,
      regional_collection='compute.forwardingRules',
      global_collection='compute.globalForwardingRules',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def ForwardingRuleArgumentPlural(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      completer=ForwardingRulesCompleter,
      plural=True,
      required=required,
      regional_collection='compute.forwardingRules',
      global_collection='compute.globalForwardingRules',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def ForwardingRuleArgumentForRoute(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      name='--next-hop-ilb',
      completer=ForwardingRulesCompleter,
      plural=False,
      required=required,
      regional_collection='compute.forwardingRules',
      short_help='Target forwarding rule that receives forwarded traffic.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def ForwardingRuleArgumentForServiceAttachment(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      name='--producer-forwarding-rule',
      completer=ForwardingRulesCompleter,
      plural=False,
      required=required,
      regional_collection='compute.forwardingRules',
      short_help='Target forwarding rule that receives forwarded traffic.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='--backend-service',
    required=False,
    resource_name='backend service',
    regional_collection='compute.regionBackendServices',
    global_collection='compute.targetBackendServices',
    short_help='Target backend service that receives the traffic.',
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


def NetworkArg():
  """Returns the network parameter."""

  load_balancing_scheme = ('--load-balancing-scheme=INTERNAL or '
                           '--load-balancing-scheme=INTERNAL_SELF_MANAGED or '
                           '--load-balancing-scheme=EXTERNAL_MANAGED (regional)'
                           ' or --load-balancing-scheme=INTERNAL_MANAGED')

  return compute_flags.ResourceArgument(
      name='--network',
      required=False,
      resource_name='network',
      global_collection='compute.networks',
      short_help='Network that this forwarding rule applies to.',
      detailed_help="""
          (Only for %s) Network that this
          forwarding rule applies to. If this field is not specified, the default
          network is used. In the absence of the default network, this field
          must be specified.
          """ % load_balancing_scheme)


SUBNET_ARG = compute_flags.ResourceArgument(
    name='--subnet',
    required=False,
    resource_name='subnetwork',
    regional_collection='compute.subnetworks',
    short_help='Subnet that this forwarding rule applies to.',
    detailed_help="""\
        (Only for --load-balancing-scheme=INTERNAL and
        --load-balancing-scheme=INTERNAL_MANAGED) Subnetwork that this
        forwarding rule applies to. If the network is auto mode, this flag is
        optional. If the network is custom mode, this flag is required.
        """,
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


IP_COLLECTION_ARG = compute_flags.ResourceArgument(
    name='--ip-collection',
    required=False,
    resource_name='public delegated prefix',
    regional_collection='compute.publicDelegatedPrefixes',
    short_help='Resource reference to a PublicDelegatedPrefix.',
    detailed_help="""
        Resource reference to a PublicDelegatedPrefix. The PDP must
        be a sub-PDP in EXTERNAL_IPV6_FORWARDING_RULE_CREATION mode.
        """,
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


def TargetGrpcProxyArg():
  """Return a resource argument for parsing a target gRPC proxy."""

  target_grpc_proxy_arg = compute_flags.ResourceArgument(
      name='--target-grpc-proxy',
      required=False,
      resource_name='target gRPC proxy',
      global_collection='compute.targetGrpcProxies',
      short_help='Target gRPC proxy that receives the traffic.',
      detailed_help=('Target gRPC proxy that receives the traffic.'),
      region_explanation=None)
  return target_grpc_proxy_arg


def TargetHttpProxyArg():
  """Return a resource argument for parsing a target http proxy."""

  target_http_proxy_arg = compute_flags.ResourceArgument(
      name='--target-http-proxy',
      required=False,
      resource_name='http proxy',
      global_collection='compute.targetHttpProxies',
      regional_collection='compute.regionTargetHttpProxies',
      short_help='Target HTTP proxy that receives the traffic.',
      detailed_help=textwrap.dedent("""\
      Target HTTP proxy that receives the traffic. For the acceptable ports, see [Port specifications](https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications).
      """),
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
  )
  return target_http_proxy_arg


def TargetHttpsProxyArg():
  """Return a resource argument for parsing a target https proxy."""

  target_https_proxy_arg = compute_flags.ResourceArgument(
      name='--target-https-proxy',
      required=False,
      resource_name='https proxy',
      global_collection='compute.targetHttpsProxies',
      regional_collection='compute.regionTargetHttpsProxies',
      short_help='Target HTTPS proxy that receives the traffic.',
      detailed_help=textwrap.dedent("""\
      Target HTTPS proxy that receives the traffic. For the acceptable ports, see [Port specifications](https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications).
      """),
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
  )
  return target_https_proxy_arg


def TargetServiceAttachmentArg():
  """Return a resource argument for parsing a target service attachment."""

  target_service_attachment_arg = compute_flags.ResourceArgument(
      name='--target-service-attachment',
      required=False,
      resource_name='target service attachment',
      regional_collection='compute.serviceAttachments',
      short_help='Target service attachment that receives the traffic.',
      detailed_help=(
          'Target service attachment that receives the traffic. '
          'The target service attachment must be in the same region as the '
          'forwarding rule.'),
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)
  return target_service_attachment_arg


TARGET_INSTANCE_ARG = compute_flags.ResourceArgument(
    name='--target-instance',
    required=False,
    resource_name='target instance',
    zonal_collection='compute.targetInstances',
    short_help='Name of the target instance that receives the traffic.',
    detailed_help=textwrap.dedent("""\
      Name of the target instance that receives the traffic. The
      target instance must be in a zone in the forwarding rule's
      region. Global forwarding rules cannot direct traffic to target
      instances.
      """) + compute_flags.ZONE_PROPERTY_EXPLANATION)

TARGET_POOL_ARG = compute_flags.ResourceArgument(
    name='--target-pool',
    required=False,
    resource_name='target pool',
    regional_collection='compute.targetPools',
    short_help='Target pool that receives the traffic.',
    detailed_help="""\
      Target pool that receives the traffic. The target pool
      must be in the same region as the forwarding rule. Global
      forwarding rules cannot direct traffic to target pools.
      """,
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))

TARGET_SSL_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-ssl-proxy',
    required=False,
    resource_name='ssl proxy',
    global_collection='compute.targetSslProxies',
    short_help='Target SSL proxy that receives the traffic.',
    detailed_help=textwrap.dedent("""\
      Target SSL proxy that receives the traffic. For the acceptable ports, see [Port specifications](https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications).
      """))


def TargetTcpProxyArg(allow_regional=False):
  """Return a resource argument for parsing a target tcp proxy."""

  target_https_proxy_arg = compute_flags.ResourceArgument(
      name='--target-tcp-proxy',
      required=False,
      resource_name='tcp proxy',
      global_collection='compute.targetTcpProxies',
      regional_collection='compute.regionTargetTcpProxies'
      if allow_regional else None,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION
      if allow_regional else None,
      short_help='Target TCP proxy that receives the traffic.',
      detailed_help=textwrap.dedent("""\
      Target TCP proxy that receives the traffic. For the acceptable ports, see [Port specifications](https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications).
      """))

  return target_https_proxy_arg


TARGET_TCP_PROXY_ARG = TargetTcpProxyArg()

TARGET_VPN_GATEWAY_ARG = compute_flags.ResourceArgument(
    name='--target-vpn-gateway',
    required=False,
    resource_name='VPN gateway',
    regional_collection='compute.targetVpnGateways',
    short_help='Target VPN gateway that receives forwarded traffic.',
    detailed_help=(
        'Target VPN gateway (Cloud VPN Classic gateway) that receives '
        'forwarded traffic. '
        'Acceptable values for --ports flag are: 500, 4500.'),
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


def AddressArgHelp():
  """Build the help text for the address argument."""

  lb_schemes = ('(EXTERNAL, EXTERNAL_MANAGED, INTERNAL, INTERNAL_SELF_MANAGED, '
                'INTERNAL_MANAGED)')

  detailed_help = """\
    The IP address that the forwarding rule serves. When a client sends traffic
    to this IP address, the forwarding rule directs the traffic to the
    target that you specify in the forwarding rule.

    If you don't specify a reserved IP address, an ephemeral IP address is
    assigned. You can specify the IP address as a literal IP address or as a
    reference to an existing Address resource. The following examples are
    all valid:
    * 100.1.2.3
    * 2600:1901::/96
    * https://compute.googleapis.com/compute/v1/projects/project-1/regions/us-central1/addresses/address-1
    * projects/project-1/regions/us-central1/addresses/address-1
    * regions/us-central1/addresses/address-1
    * global/addresses/address-1
    * address-1

    The load-balancing-scheme %s and the target of the forwarding rule
    determine the type of IP address that you can use. The address
    type must be external for load-balancing-scheme EXTERNAL or
    EXTERNAL_MANAGED. For other load-balancing-schemes, the address type
    must be internal. For detailed information, refer to
    https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#ip_address_specifications.
  """ % (
      lb_schemes)

  return textwrap.dedent(detailed_help)


def AddressArg():
  return compute_flags.ResourceArgument(
      name='--address',
      required=False,
      resource_name='address',
      completer=addresses_flags.AddressesCompleter,
      regional_collection='compute.addresses',
      global_collection='compute.globalAddresses',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
      short_help='IP address that the forwarding rule will serve.',
      detailed_help=AddressArgHelp())


def AddUpdateTargetArgs(parser,
                        include_psc_google_apis=False,
                        include_target_service_attachment=False,
                        include_regional_tcp_proxy=False):
  """Adds common flags for mutating forwarding rule targets."""
  target = parser.add_mutually_exclusive_group(required=True)

  TargetGrpcProxyArg().AddArgument(parser, mutex_group=target)

  if include_target_service_attachment:
    TargetServiceAttachmentArg().AddArgument(parser, mutex_group=target)

  TargetHttpProxyArg().AddArgument(parser, mutex_group=target)
  TargetHttpsProxyArg().AddArgument(parser, mutex_group=target)
  TARGET_INSTANCE_ARG.AddArgument(parser, mutex_group=target)
  TARGET_POOL_ARG.AddArgument(parser, mutex_group=target)
  TARGET_SSL_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TargetTcpProxyArg(allow_regional=include_regional_tcp_proxy).AddArgument(
      parser, mutex_group=target)
  TARGET_VPN_GATEWAY_ARG.AddArgument(parser, mutex_group=target)
  BACKEND_SERVICE_ARG.AddArgument(parser, mutex_group=target)

  if include_psc_google_apis:
    target.add_argument(
        '--target-google-apis-bundle',
        required=False,
        help=(
            'Target bundle of Google APIs that will receive forwarded traffic '
            'via Private Service Connect. '
            'Acceptable values are all-apis, meaning all Google APIs, or '
            'vpc-sc, meaning just the APIs that support VPC Service Controls'),
        action='store')


def AddCreateArgs(parser,
                  include_psc_google_apis=False,
                  include_target_service_attachment=False,
                  include_regional_tcp_proxy=False,
                  include_ip_collection=False):
  """Adds common flags for creating forwarding rules."""
  AddUpdateTargetArgs(parser, include_psc_google_apis,
                      include_target_service_attachment,
                      include_regional_tcp_proxy)

  NetworkArg().AddArgument(parser)
  SUBNET_ARG.AddArgument(parser)

  if include_ip_collection:
    IP_COLLECTION_ARG.AddArgument(parser)

  AddLoadBalancingScheme(
      parser,
      include_psc_google_apis=include_psc_google_apis,
      include_target_service_attachment=include_target_service_attachment,
      include_regional_tcp_proxy=include_regional_tcp_proxy)


def AddSetTargetArgs(parser,
                     include_psc_google_apis=False,
                     include_target_service_attachment=False,
                     include_regional_tcp_proxy=False):
  """Adds flags for the set-target command."""
  AddUpdateTargetArgs(parser, include_psc_google_apis,
                      include_target_service_attachment,
                      include_regional_tcp_proxy)

  # The argument below are deprecated and will be eventually removed.
  def CreateDeprecationAction(name):
    return actions.DeprecationAction(
        name,
        warn=('The {flag_name} option is deprecated and will be removed in '
              'an upcoming release. If you\'re currently using this argument, '
              'you should remove it from your workflows.'),
        removed=False,
        action='store')

  parser.add_argument(
      '--network',
      required=False,
      help=('Only for --load-balancing-scheme=INTERNAL or '
            '--load-balancing-scheme=INTERNAL_SELF_MANAGED or '
            '--load-balancing-scheme=EXTERNAL_MANAGED (regional) or '
            '--load-balancing-scheme=INTERNAL_MANAGED) Network that this '
            'forwarding rule applies to. If this field is not specified, '
            'the default network is used. In the absence of the default '
            'network, this field must be specified.'),
      action=CreateDeprecationAction('--network'))

  parser.add_argument(
      '--subnet',
      required=False,
      help=(
          'Only for --load-balancing-scheme=INTERNAL and '
          '--load-balancing-scheme=INTERNAL_MANAGED) Subnetwork that this '
          'forwarding rule applies to. If the network is auto mode, this flag '
          'is optional. If the network is custom mode, this flag is required.'),
      action=CreateDeprecationAction('--subnet'))

  parser.add_argument(
      '--subnet-region',
      required=False,
      help=('Region of the subnetwork to operate on. If not specified, the '
            'region is set to the region of the forwarding rule. Overrides '
            'the default compute/region property value for this command '
            'invocation.'),
      action=CreateDeprecationAction('--subnet-region'))

  AddLoadBalancingScheme(
      parser,
      include_psc_google_apis=include_psc_google_apis,
      include_target_service_attachment=include_target_service_attachment,
      include_regional_tcp_proxy=include_regional_tcp_proxy,
      deprecation_action=CreateDeprecationAction('--load-balancing-scheme'))


def AddLoadBalancingScheme(parser,
                           include_psc_google_apis=False,
                           include_target_service_attachment=False,
                           include_regional_tcp_proxy=False,
                           deprecation_action=None):
  """Adds the load-balancing-scheme flag."""
  td_proxies = ('--target-http-proxy, --target-https-proxy, '
                '--target-grpc-proxy, --target-tcp-proxy')
  ilb_proxies = ('--target-http-proxy, --target-https-proxy')
  if include_regional_tcp_proxy:
    ilb_proxies += (', --target-tcp-proxy')
  load_balancing_choices = {
      'EXTERNAL':
          'Classic Application Load Balancers, global external proxy Network '
          ' Load Balancers, external passthrough Network Load Balancers or '
          ' protocol forwarding, used with one of '
          '--target-http-proxy, --target-https-proxy, --target-tcp-proxy, '
          '--target-ssl-proxy, --target-pool, --target-vpn-gateway, '
          '--target-instance.',
      'EXTERNAL_MANAGED':
          'Global and regional external Application Load Balancers, and '
          'regional external proxy Network Load Balancers, used with '
          '--target-http-proxy, --target-https-proxy, --target-tcp-proxy.',
      'INTERNAL':
          'Internal passthrough Network Load Balancers or protocol '
          'forwarding, used with --backend-service.',
      'INTERNAL_SELF_MANAGED':
          'Traffic Director, used with {0}.'.format(td_proxies),
      'INTERNAL_MANAGED':
          'Internal Application Load Balancers and internal proxy Network '
          'Load Balancers, used with {0}.'.format(ilb_proxies)
  }

  # There isn't a default load-balancing-scheme for PSC forwarding rules.
  # But the default is EXTERNAL for non-PSC forwarding rules.
  include_psc = (include_psc_google_apis or include_target_service_attachment)
  parser.add_argument(
      '--load-balancing-scheme',
      choices=load_balancing_choices,
      type=lambda x: x.replace('-', '_').upper(),
      default=None if include_psc else 'EXTERNAL',
      help="This defines the forwarding rule's load balancing scheme. Note that it defaults to EXTERNAL and is not applicable for Private Service Connect forwarding rules."
      if include_psc else
      "This defines the forwarding rule's load balancing scheme.",
      action=deprecation_action)


def SourceIpRangesParser(string_value):
  type_parse = arg_parsers.ArgList(min_length=1)
  return type_parse(string_value)


def AddSourceIpRanges(parser):
  """Adds source-ip-ranges flag to the argparse.

  Args:
    parser: The parser that parses args from user input.
  """
  parser.add_argument(
      '--source-ip-ranges',
      metavar='SOURCE_IP_RANGE,[...]',
      type=SourceIpRangesParser,
      default=None,
      help="""\
      List of comma-separated IP addresses or IP ranges. If set, this forwarding
      rule only forwards traffic when the packet's source IP address matches one
      of the IP ranges set here.
      """)


def AddAllowGlobalAccess(parser):
  """Adds allow global access flag to the argparse."""
  parser.add_argument(
      '--allow-global-access',
      action='store_true',
      default=None,
      help="""\
      If True, then clients from all regions can access this internal
      forwarding rule. This can only be specified for forwarding rules with
      the LOAD_BALANCING_SCHEME set to INTERNAL or INTERNAL_MANAGED. For
      forwarding rules of type INTERNAL, the target must be either a backend
      service or a target instance.
      """)


def AddAllowPscGlobalAccess(parser):
  """Adds allow PSC global access flag to the argparse."""
  parser.add_argument(
      '--allow-psc-global-access',
      action='store_true',
      default=None,
      help="""\
      If specified, clients from all regions can access this Private
      Service Connect forwarding rule. This can only be specified if the
      forwarding rule's target is a service attachment
      (--target-service-attachment).
      """)


def AddDisableAutomateDnsZone(parser):
  """Adds disable automate dns zone flag to the argparse."""
  parser.add_argument(
      '--disable-automate-dns-zone',
      action='store_true',
      default=None,
      help="""\
      If specified, then a DNS zone will not be auto-generated for this Private
      Service Connect forwarding rule. This can only be specified if the
      forwarding rule's target is a service attachment
      (`--target-service-attachment=SERVICE_ATTACHMENT`) or Google APIs bundle
      (`--target-google-apis-bundle=API_BUNDLE`)
      """)


def AddIPProtocols(parser, support_all_protocol, support_l3_default):
  """Adds IP protocols flag, with values available in the given version.

  Args:
    parser: The parser that parses args from user input.
    support_all_protocol: Whether to include "ALL" in the protocols list.
    support_l3_default: Whether to include "L3_DEFAULT" in the protocols list.
  """

  protocols = ['AH', 'ESP', 'ICMP', 'SCTP', 'TCP', 'UDP']
  if support_l3_default:
    protocols.append('L3_DEFAULT')
  if support_all_protocol:
    protocols.append('ALL')
    if support_l3_default:
      help_str = """\
        IP protocol that the rule will serve. The default is `TCP`.

        Note that if the load-balancing scheme is `INTERNAL`, the protocol must
        be one of: `TCP`, `UDP`, `ALL`, `L3_DEFAULT`.

        For a load-balancing scheme that is `EXTERNAL`, all IP_PROTOCOL
        options other than `ALL` are valid.
        """
    else:
      help_str = """\
        IP protocol that the rule will serve. The default is `TCP`.

        Note that if the load-balancing scheme is `INTERNAL`, the protocol must
        be one of: `TCP`, `UDP`, `ALL`.

        For a load-balancing scheme that is `EXTERNAL`, all IP_PROTOCOL
        options other than `ALL` are valid.
        """
  else:
    if support_l3_default:
      help_str = """\
        IP protocol that the rule will serve. The default is `TCP`.

        Note that if the load-balancing scheme is `INTERNAL`, the protocol must
        be one of: `TCP`, `UDP`, `L3_DEFAULT`.

        For a load-balancing scheme that is `EXTERNAL`, all IP_PROTOCOL
        options are valid.
        """
    else:
      help_str = """\
        IP protocol that the rule will serve. The default is `TCP`.

        Note that if the load-balancing scheme is `INTERNAL`, the protocol must
        be one of: `TCP`, `UDP`.

        For a load-balancing scheme that is `EXTERNAL`, all IP_PROTOCOL
        options are valid.
        """

  parser.add_argument(
      '--ip-protocol',
      choices=protocols,
      type=lambda x: x.upper(),
      help=help_str)


def AddAddressesAndIPVersions(parser):
  """Adds Addresses and IP versions flag."""

  address_arg = AddressArg()
  address_arg.AddArgument(parser)
  parser.add_argument(
      '--ip-version',
      choices=['IPV4', 'IPV6'],
      type=lambda x: x.upper(),
      help="""\
      Version of the IP address to be allocated or assigned.
      The default is IPv4.
      """)


def AddDescription(parser):
  """Adds description flag."""

  parser.add_argument(
      '--description',
      help='Optional textual description for the forwarding rule.')


def AddPortsAndPortRange(parser):
  """Adds ports and port range flags."""

  ports_scope = parser.add_mutually_exclusive_group()
  ports_metavar = 'ALL | [PORT | START_PORT-END_PORT],[...]'
  ports_help = """\
  List of comma-separated ports. The forwarding rule forwards packets with
  matching destination ports. Port specification requirements vary
  depending on the load-balancing scheme and target.
  For more information, refer to https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications.
  """

  ports_scope.add_argument(
      '--ports',
      metavar=ports_metavar,
      type=PortRangesWithAll.CreateParser(),
      default=None,
      help=ports_help)

  ports_scope.add_argument(
      '--port-range',
      type=arg_parsers.Range.Parse,
      metavar='[PORT | START_PORT-END_PORT]',
      help="""\
      DEPRECATED, use --ports. If specified, only packets addressed to ports in
      the specified range are forwarded. For more information, refer to
      https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications.
      """)


def AddNetworkTier(parser, supports_network_tier_flag, for_update):
  """Adds network tier flag."""

  # This arg is a string simulating enum NetworkTier because one of the
  # option SELECT is hidden since it's not advertised to all customers.
  if supports_network_tier_flag:
    if for_update:
      parser.add_argument(
          '--network-tier',
          type=lambda x: x.upper(),
          help="""\
          Update the network tier of a forwarding rule. It does not allow to
          change from `PREMIUM` to `STANDARD` and visa versa.
          """)
    else:
      parser.add_argument(
          '--network-tier',
          type=lambda x: x.upper(),
          help="""\
          Network tier to assign to the forwarding rules. ``NETWORK_TIER''
          must be one of: `PREMIUM`, `STANDARD`, `FIXED_STANDARD`.
          The default value is `PREMIUM`.
          """)


def AddIsMirroringCollector(parser):
  parser.add_argument(
      '--is-mirroring-collector',
      action='store_true',
      default=None,
      help="""\
      If set, this forwarding rule can be used as a collector for packet
      mirroring. This can only be specified for forwarding rules with the
      LOAD_BALANCING_SCHEME set to INTERNAL.
      """)


def AddServiceDirectoryRegistration(parser):
  """Adds service-directory-registration flag to the argparse."""
  parser.add_argument(
      '--service-directory-registration',
      type=str,
      action='store',
      default=None,
      help="""\
      The Service Directory service in which to register this forwarding rule as
      an endpoint. The Service Directory service must be in the same project and
      region as the forwarding rule you are creating.
      """)


class PortRangesWithAll(object):
  """Particular keyword 'all' or a range of integer values."""

  def __init__(self, all_specified, ranges):
    self.all_specified = all_specified
    self.ranges = ranges

  @staticmethod
  def CreateParser():
    """Creates parser to parse keyword 'all' first before parse range."""

    def _Parse(string_value):
      if string_value.lower() == 'all':
        return PortRangesWithAll(True, [])
      else:
        type_parse = arg_parsers.ArgList(
            min_length=1, element_type=arg_parsers.Range.Parse)
        return PortRangesWithAll(False, type_parse(string_value))

    return _Parse
