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
"""Command for creating forwarding rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress
import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import exceptions as fw_exceptions
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.core import log
import six
from six.moves import range  # pylint: disable=redefined-builtin


def _Args(
    parser,
    support_global_access,
    support_psc_google_apis,
    support_all_protocol,
    support_target_service_attachment,
    support_l3_default,
    support_source_ip_range,
    support_disable_automate_dns_zone,
    support_regional_tcp_proxy,
    support_ip_collection,
):
  """Add the flags to create a forwarding rule."""

  flags.AddCreateArgs(
      parser,
      include_psc_google_apis=support_psc_google_apis,
      include_target_service_attachment=support_target_service_attachment,
      include_regional_tcp_proxy=support_regional_tcp_proxy,
      include_ip_collection=support_ip_collection)
  flags.AddIPProtocols(parser, support_all_protocol, support_l3_default)
  flags.AddDescription(parser)
  flags.AddPortsAndPortRange(parser)
  flags.AddNetworkTier(
      parser, supports_network_tier_flag=True, for_update=False)

  if support_global_access:
    flags.AddAllowGlobalAccess(parser)

  flags.AddAllowPscGlobalAccess(parser)

  if support_source_ip_range:
    flags.AddSourceIpRanges(parser)

  if support_disable_automate_dns_zone:
    flags.AddDisableAutomateDnsZone(parser)

  flags.AddIsMirroringCollector(parser)
  flags.AddServiceDirectoryRegistration(parser)

  parser.add_argument(
      '--service-label',
      help='(Only for Internal Load Balancing): '
      'https://cloud.google.com/load-balancing/docs/dns-names/\n'
      'The DNS label to use as the prefix of the fully qualified domain '
      'name for this forwarding rule. The full name will be internally '
      'generated and output as dnsName. If this field is not specified, '
      'no DNS record will be generated and no DNS name will be output. '
      'You cannot use the `--service-label` flag  if the forwarding rule '
      'references an internal IP address that has the '
      '`--purpose=SHARED_LOADBALANCER_VIP` flag set.')
  flags.AddAddressesAndIPVersions(parser)
  forwarding_rule_arg = flags.ForwardingRuleArgument()
  forwarding_rule_arg.AddArgument(parser, operation_type='create')
  parser.display_info.AddCacheUpdater(flags.ForwardingRulesCompleter)
  return forwarding_rule_arg


class CreateHelper(object):
  """Helper class to create a forwarding rule."""

  FORWARDING_RULE_ARG = None

  def __init__(
      self,
      holder,
      support_global_access,
      support_psc_google_apis,
      support_all_protocol,
      support_target_service_attachment,
      support_sd_registration_for_regional,
      support_l3_default,
      support_source_ip_range,
      support_disable_automate_dns_zone,
      support_regional_tcp_proxy,
      support_ip_collection
  ):
    self._holder = holder
    self._support_global_access = support_global_access
    self._support_psc_google_apis = support_psc_google_apis
    self._support_all_protocol = support_all_protocol
    self._support_target_service_attachment = support_target_service_attachment
    self._support_sd_registration_for_regional = (
        support_sd_registration_for_regional
    )
    self._support_l3_default = support_l3_default
    self._support_source_ip_range = support_source_ip_range
    self._support_disable_automate_dns_zone = support_disable_automate_dns_zone
    self._support_regional_tcp_proxy = support_regional_tcp_proxy
    self._support_ip_collection = support_ip_collection

  @classmethod
  def Args(
      cls,
      parser,
      support_global_access,
      support_psc_google_apis,
      support_all_protocol,
      support_target_service_attachment,
      support_l3_default,
      support_source_ip_range,
      support_disable_automate_dns_zone,
      support_regional_tcp_proxy,
      support_ip_collection
  ):
    """Inits the class args for supported features."""
    cls.FORWARDING_RULE_ARG = _Args(
        parser,
        support_global_access,
        support_psc_google_apis,
        support_all_protocol,
        support_target_service_attachment,
        support_l3_default,
        support_source_ip_range,
        support_disable_automate_dns_zone,
        support_regional_tcp_proxy,
        support_ip_collection
    )

  def ConstructProtocol(self, messages, args):
    if args.ip_protocol:
      return messages.ForwardingRule.IPProtocolValueValuesEnum(args.ip_protocol)
    else:
      return

  def Run(self, args):
    """Issues requests necessary to create Forwarding Rules."""
    client = self._holder.client

    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        self._holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
      requests = self._CreateGlobalRequests(client, self._holder.resources,
                                            args, forwarding_rule_ref)
    elif forwarding_rule_ref.Collection() == 'compute.forwardingRules':
      requests = self._CreateRegionalRequests(client, self._holder.resources,
                                              args, forwarding_rule_ref)

    return client.MakeRequests(requests)

  def _CreateGlobalRequests(self, client, resources, args, forwarding_rule_ref):
    """Create a globally scoped request."""

    is_psc_google_apis = False
    if hasattr(args,
               'target_google_apis_bundle') and args.target_google_apis_bundle:
      if not self._support_psc_google_apis:
        raise exceptions.InvalidArgumentException(
            '--target-google-apis-bundle',
            'Private Service Connect for Google APIs (the target-google-apis-bundle option '
            'for forwarding rules) is not supported in this API version.')
      else:
        is_psc_google_apis = True

    sd_registration = None
    if hasattr(args, 'service_directory_registration'
              ) and args.service_directory_registration:
      if not is_psc_google_apis:
        raise exceptions.InvalidArgumentException(
            '--service-directory-registration',
            'Can only be specified for regional forwarding rules or Private Service Connect forwarding rules targeting a Google APIs bundle.'
        )
      # Parse projects/../locations/..
      match = re.match(
          r'^projects/([^/]+)/locations/([^/]+)(?:/namespaces/([^/]+))?$',
          args.service_directory_registration)
      if not match:
        raise exceptions.InvalidArgumentException(
            '--service-directory-registration',
            'Must be of the form projects/PROJECT/locations/REGION or projects/PROJECT/locations/REGION/namespaces/NAMESPACE'
        )
      project = match.group(1)
      region = match.group(2)
      namespace = match.group(3)

      if project != forwarding_rule_ref.project:
        raise exceptions.InvalidArgumentException(
            '--service-directory-registration',
            'Must be in the same project as the forwarding rule.')

      sd_registration = client.messages.ForwardingRuleServiceDirectoryRegistration(
          serviceDirectoryRegion=region, namespace=namespace)

    ports_all_specified, range_list = _ExtractPortsAndAll(args.ports)
    port_range = _MakeSingleUnifiedPortRange(args.port_range, range_list)
    # All global forwarding rules must use EXTERNAL or INTERNAL_SELF_MANAGED
    # schemes presently.
    load_balancing_scheme = _GetLoadBalancingScheme(args, client.messages,
                                                    is_psc_google_apis)
    if (load_balancing_scheme == client.messages.ForwardingRule
        .LoadBalancingSchemeValueValuesEnum.INTERNAL):
      raise fw_exceptions.ArgumentError(
          'You cannot specify internal [--load-balancing-scheme] for a global '
          'forwarding rule.')

    if (load_balancing_scheme == client.messages.ForwardingRule
        .LoadBalancingSchemeValueValuesEnum.INTERNAL_SELF_MANAGED):
      if (not args.target_http_proxy and not args.target_https_proxy and
          not args.target_grpc_proxy and not args.target_tcp_proxy):
        target_error_message_with_tcp = (
            'You must specify either [--target-http-proxy], '
            '[--target-https-proxy], [--target-grpc-proxy] '
            'or [--target-tcp-proxy] for an '
            'INTERNAL_SELF_MANAGED [--load-balancing-scheme].')
        raise fw_exceptions.ArgumentError(target_error_message_with_tcp)

      if args.subnet:
        raise fw_exceptions.ArgumentError(
            'You cannot specify [--subnet] for an INTERNAL_SELF_MANAGED '
            '[--load-balancing-scheme].')

      if not args.address:
        raise fw_exceptions.ArgumentError(
            'You must specify [--address] for an INTERNAL_SELF_MANAGED '
            '[--load-balancing-scheme]')

    if is_psc_google_apis:
      rule_name = forwarding_rule_ref.Name()
      if len(rule_name) > 20 or rule_name[0].isdigit(
      ) or not rule_name.isalnum():
        raise fw_exceptions.ArgumentError(
            'A forwarding rule to Google APIs must have a name that is between '
            ' 1-20 characters long, alphanumeric, starting with a letter.')

      if port_range:
        raise exceptions.InvalidArgumentException(
            '--ports',
            '[--ports] is not allowed for PSC-GoogleApis forwarding rules.')
      if load_balancing_scheme:
        raise exceptions.InvalidArgumentException(
            '--load-balancing-scheme',
            'The --load-balancing-scheme flag is not allowed for PSC-GoogleApis'
            ' forwarding rules.')

      if args.target_google_apis_bundle in flags.PSC_GOOGLE_APIS_BUNDLES:
        target_as_str = args.target_google_apis_bundle
      else:
        bundles_list = ', '.join(flags.PSC_GOOGLE_APIS_BUNDLES)
        raise exceptions.InvalidArgumentException(
            '--target-google-apis-bundle',
            'The valid values for target-google-apis-bundle are: ' +
            bundles_list)
    else:
      # L7XLB in Premium Tier.
      target_ref = utils.GetGlobalTarget(resources, args)
      target_as_str = target_ref.SelfLink()

      if ports_all_specified:
        raise exceptions.InvalidArgumentException(
            '--ports',
            '[--ports] cannot be set to ALL for global forwarding rules.')
      if not port_range:
        raise exceptions.InvalidArgumentException(
            '--ports', '[--ports] is required for global forwarding rules.')

    protocol = self.ConstructProtocol(client.messages, args)

    address = self._ResolveAddress(resources, args,
                                   compute_flags.compute_scope.ScopeEnum.GLOBAL,
                                   forwarding_rule_ref)
    forwarding_rule = client.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        portRange=port_range,
        target=target_as_str,
        networkTier=_ConstructNetworkTier(client.messages, args),
        loadBalancingScheme=load_balancing_scheme)

    self._ProcessCommonArgs(client, resources, args, forwarding_rule_ref,
                            forwarding_rule)
    if sd_registration:
      forwarding_rule.serviceDirectoryRegistrations.append(sd_registration)

    if self._support_global_access and args.IsSpecified('allow_global_access'):
      forwarding_rule.allowGlobalAccess = args.allow_global_access

    request = client.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule, project=forwarding_rule_ref.project)

    return [(client.apitools_client.globalForwardingRules, 'Insert', request)]

  def _CreateRegionalRequests(self, client, resources, args,
                              forwarding_rule_ref):
    """Create a regionally scoped request."""
    is_psc_ilb = False
    if hasattr(args,
               'target_service_attachment') and args.target_service_attachment:
      if not self._support_target_service_attachment:
        raise exceptions.InvalidArgumentException(
            '--target-service-attachment',
            'Private Service Connect for ILB (the target-service-attachment '
            'option) is not supported in this API version.')
      else:
        is_psc_ilb = True

    target_ref, region_ref = utils.GetRegionalTarget(
        client,
        resources,
        args,
        forwarding_rule_ref,
        include_regional_tcp_proxy=self._support_regional_tcp_proxy,
        include_target_service_attachment=self
        ._support_target_service_attachment)

    if not args.region and region_ref:
      args.region = region_ref

    protocol = self.ConstructProtocol(client.messages, args)

    address = self._ResolveAddress(resources, args,
                                   compute_flags.compute_scope.ScopeEnum.REGION,
                                   forwarding_rule_ref)

    load_balancing_scheme = _GetLoadBalancingScheme(args, client.messages,
                                                    is_psc_ilb)

    if is_psc_ilb and load_balancing_scheme:
      raise exceptions.InvalidArgumentException(
          '--load-balancing-scheme',
          'The --load-balancing-scheme flag is not allowed for PSC-ILB '
          'forwarding rules.')

    if (load_balancing_scheme == client.messages.ForwardingRule
        .LoadBalancingSchemeValueValuesEnum.INTERNAL):
      if args.port_range:
        raise fw_exceptions.ArgumentError(
            'You cannot specify [--port-range] for a forwarding rule '
            'whose [--load-balancing-scheme] is internal, '
            'please use [--ports] flag instead.')

    if (load_balancing_scheme == client.messages.ForwardingRule
        .LoadBalancingSchemeValueValuesEnum.INTERNAL_SELF_MANAGED):
      raise fw_exceptions.ArgumentError(
          'You cannot specify an INTERNAL_SELF_MANAGED '
          '[--load-balancing-scheme] for a regional forwarding rule.')

    forwarding_rule = client.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        networkTier=_ConstructNetworkTier(client.messages, args),
        loadBalancingScheme=load_balancing_scheme)
    if self._support_source_ip_range and args.source_ip_ranges:
      forwarding_rule.sourceIpRanges = args.source_ip_ranges

    self._ProcessCommonArgs(client, resources, args, forwarding_rule_ref,
                            forwarding_rule)

    ports_all_specified, range_list = _ExtractPortsAndAll(args.ports)

    if target_ref.Collection() == 'compute.regionBackendServices':
      # A FR pointing to a BES has no target attribute.
      forwarding_rule.backendService = target_ref.SelfLink()
      forwarding_rule.target = None
    else:
      # A FR pointing to anything not a BES has a target attribute.
      forwarding_rule.backendService = None
      forwarding_rule.target = target_ref.SelfLink()

    if ((target_ref.Collection() == 'compute.regionBackendServices' or
         target_ref.Collection() == 'compute.targetInstances') and
        args.load_balancing_scheme == 'INTERNAL'):
      # This is for L4ILB and internal protocol forwarding.
      # API fields allPorts, ports, and portRange are mutually exclusive.
      # API field portRange is not valid for this case.
      # Use of L3_DEFAULT implies all ports even if allPorts is unset.
      if ports_all_specified:
        forwarding_rule.allPorts = True
      elif range_list:
        forwarding_rule.ports = [
            six.text_type(p) for p in _GetPortList(range_list)
        ]
    elif ((target_ref.Collection() == 'compute.regionTargetHttpProxies' or
           target_ref.Collection() == 'compute.regionTargetHttpsProxies') and
          args.load_balancing_scheme == 'INTERNAL'):
      # This is a legacy configuration for L7ILB.
      forwarding_rule.ports = [
          six.text_type(p) for p in _GetPortList(range_list)
      ]
    elif args.load_balancing_scheme == 'INTERNAL':
      # There are currently no other valid combinations of targets with scheme
      # internal. With scheme internal, targets must presently be a regional
      # backend service (L4ILB) or a target instance (protocol forwarding).
      raise exceptions.InvalidArgumentException(
          '--load-balancing-scheme',
          'Only target instances and backend services should be specified as '
          'a target for internal load balancing.')
    elif args.load_balancing_scheme == 'INTERNAL_MANAGED':
      # This is L7ILB.
      forwarding_rule.portRange = _MakeSingleUnifiedPortRange(
          args.port_range, range_list)
    elif args.load_balancing_scheme == 'EXTERNAL_MANAGED':
      # This is regional L7XLB.
      forwarding_rule.portRange = _MakeSingleUnifiedPortRange(
          args.port_range, range_list)
    elif ((target_ref.Collection() == 'compute.regionBackendServices') and
          ((args.load_balancing_scheme == 'EXTERNAL') or
           (not args.load_balancing_scheme))):
      # This is NetLB using a backend service. Scheme is either explicitly
      # EXTERNAL or not supplied (EXTERNAL is the default scheme).
      # API fields allPorts, ports, and portRange are mutually exclusive.
      # All three API fields are valid for this case.
      # Use of L3_DEFAULT implies all ports even if allPorts is unset.
      if ports_all_specified:
        forwarding_rule.allPorts = True
      elif range_list:
        if len(range_list) > 1:
          # More than one port, potentially discontiguous, from --ports= flag.
          forwarding_rule.ports = [
              six.text_type(p) for p in _GetPortList(range_list)
          ]
        else:
          # Exactly one value from --ports= flag. Might be a single port (80);
          # might be a range (80-90). Since it might be a range, the portRange
          # API attribute is more appropriate.
          forwarding_rule.portRange = six.text_type(range_list[0])
      elif args.port_range:
        forwarding_rule.portRange = _MakeSingleUnifiedPortRange(
            args.port_range, range_list)
    elif ((target_ref.Collection() == 'compute.targetPool' or
           target_ref.Collection() == 'compute.targetInstances') and
          ((args.load_balancing_scheme == 'EXTERNAL') or
           (not args.load_balancing_scheme))):
      # This is NetLB using a target pool or external protocol forwarding.
      # Scheme is either explicitly EXTERNAL or not supplied (EXTERNAL is the
      # default scheme).
      # API fields allPorts, ports, and portRange are mutually exclusive.
      # API field ports is not valid for this case.
      # Use of L3_DEFAULT implies all ports by definition.
      if ports_all_specified:
        forwarding_rule.allPorts = True
      else:
        forwarding_rule.portRange = _MakeSingleUnifiedPortRange(
            args.port_range, range_list)
    else:
      # All other regional forwarding rules with load balancing scheme EXTERNAL.
      forwarding_rule.portRange = _MakeSingleUnifiedPortRange(
          args.port_range, range_list)

    if hasattr(args, 'service_label'):
      forwarding_rule.serviceLabel = args.service_label

    if self._support_global_access and args.IsSpecified('allow_global_access'):
      forwarding_rule.allowGlobalAccess = args.allow_global_access

    if args.IsSpecified('allow_psc_global_access'):
      forwarding_rule.allowPscGlobalAccess = args.allow_psc_global_access

    if self._support_ip_collection and args.ip_collection:
      forwarding_rule.ipCollection = flags.IP_COLLECTION_ARG.ResolveAsResource(
          args, resources).SelfLink()

    if self._support_disable_automate_dns_zone and args.IsSpecified(
        'disable_automate_dns_zone'):
      forwarding_rule.noAutomateDnsZone = args.disable_automate_dns_zone

    if hasattr(args, 'is_mirroring_collector'):
      forwarding_rule.isMirroringCollector = args.is_mirroring_collector

    if hasattr(args, 'service_directory_registration'
              ) and args.service_directory_registration:
      if is_psc_ilb:
        # Parse projects/../locations/../namespaces/..
        match = re.match(
            r'^projects/([^/]+)/locations/([^/]+)/namespaces/([^/]+)$',
            args.service_directory_registration)
        if not match:
          raise exceptions.InvalidArgumentException(
              '--service-directory-registration',
              'If set, must be of the form projects/PROJECT/locations/REGION/namespaces/NAMESPACE'
          )
        project = match.group(1)
        region = match.group(2)

        if project != forwarding_rule_ref.project or region != forwarding_rule_ref.region:
          raise exceptions.InvalidArgumentException(
              '--service-directory-registration',
              'Service Directory registration must be in the same project and region as the forwarding rule.'
          )

        sd_registration = client.messages.ForwardingRuleServiceDirectoryRegistration(
            namespace=match.group(3))
        forwarding_rule.serviceDirectoryRegistrations.append(sd_registration)
      else:
        if not self._support_sd_registration_for_regional:
          raise exceptions.InvalidArgumentException(
              '--service-directory-registration',
              """flag is available in one or more alternate release tracks. Try:

  gcloud alpha compute forwarding-rules create --service-directory-registration
  gcloud beta compute forwarding-rules create --service-directory-registration"""
          )
        # Parse projects/../locations/../namespaces/../services/..
        match = re.match(
            r'^projects/([^/]+)/locations/([^/]+)/namespaces/([^/]+)/services/([^/]+)$',
            args.service_directory_registration)
        if not match:
          raise exceptions.InvalidArgumentException(
              '--service-directory-registration',
              'Must be of the form projects/PROJECT/locations/REGION/namespaces/NAMESPACE/services/SERVICE'
          )
        project = match.group(1)
        region = match.group(2)

        if project != forwarding_rule_ref.project or region != forwarding_rule_ref.region:
          raise exceptions.InvalidArgumentException(
              '--service-directory-registration',
              'Service Directory registration must be in the same project and region as the forwarding rule.'
          )

        sd_registration = client.messages.ForwardingRuleServiceDirectoryRegistration(
            namespace=match.group(3), service=match.group(4))
        forwarding_rule.serviceDirectoryRegistrations.append(sd_registration)

    request = client.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=forwarding_rule_ref.project,
        region=forwarding_rule_ref.region)

    return [(client.apitools_client.forwardingRules, 'Insert', request)]

  def _ResolveAddress(self, resources, args, scope, forwarding_rule_ref):
    """Resolve address resource."""

    # Address takes either an ip address or an address resource. If parsing as
    # an IP address fails, then we resolve as a resource.
    address = args.address
    if address is not None:
      try:
        # ipaddress only allows unicode input
        ipaddress.ip_network(six.text_type(args.address))
      except ValueError:
        # TODO(b/37086838): Make sure global/region settings are inherited by
        # address resource.
        if scope == compute_flags.compute_scope.ScopeEnum.REGION:
          if not args.global_address and not args.address_region:
            if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
              args.address_region = forwarding_rule_ref.region
        address_ref = flags.AddressArg().ResolveAsResource(
            args, resources, default_scope=scope)
        address = address_ref.SelfLink()

    return address

  def _ProcessCommonArgs(self, client, resources, args, forwarding_rule_ref,
                         forwarding_rule):
    """Processes common arguments for global and regional commands.

    Args:
      client: The client used by gcloud.
      resources: The resource parser.
      args: The arguments passed to the gcloud command.
      forwarding_rule_ref: The forwarding rule reference.
      forwarding_rule: The forwarding rule to set properties on.
    """

    if args.ip_version:
      forwarding_rule.ipVersion = (
          client.messages.ForwardingRule.IpVersionValueValuesEnum(
              args.ip_version))
    if args.network:
      forwarding_rule.network = flags.NetworkArg().ResolveAsResource(
          args, resources).SelfLink()
    if args.subnet:
      if (not args.subnet_region and
          forwarding_rule_ref.Collection() == 'compute.forwardingRules'):
        args.subnet_region = forwarding_rule_ref.region
      forwarding_rule.subnetwork = flags.SUBNET_ARG.ResolveAsResource(
          args, resources).SelfLink()


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  _support_global_access = True
  _support_psc_google_apis = True
  _support_all_protocol = False
  _support_target_service_attachment = True
  _support_sd_registration_for_regional = False
  _support_l3_default = True
  _support_source_ip_range = True
  _support_disable_automate_dns_zone = True
  _support_regional_tcp_proxy = True
  _support_ip_collection = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(parser, cls._support_global_access,
                      cls._support_psc_google_apis, cls._support_all_protocol,
                      cls._support_target_service_attachment,
                      cls._support_l3_default, cls._support_source_ip_range,
                      cls._support_disable_automate_dns_zone,
                      cls._support_regional_tcp_proxy,
                      cls._support_ip_collection)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return CreateHelper(
        holder,
        self._support_global_access,
        self._support_psc_google_apis,
        self._support_all_protocol,
        self._support_target_service_attachment,
        self._support_sd_registration_for_regional,
        self._support_l3_default,
        self._support_source_ip_range,
        self._support_disable_automate_dns_zone,
        self._support_regional_tcp_proxy,
        self._support_ip_collection,
    ).Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""
  _support_global_access = True
  _support_all_protocol = False
  _support_target_service_attachment = True
  _support_sd_registration_for_regional = True
  _support_l3_default = True
  _support_source_ip_range = True
  _support_disable_automate_dns_zone = True
  _support_regional_tcp_proxy = True
  _support_ip_collection = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a forwarding rule to direct network traffic to a load balancer."""
  _support_global_access = True
  _support_all_protocol = True
  _support_target_service_attachment = True
  _support_sd_registration_for_regional = True
  _support_l3_default = True
  _support_source_ip_range = True
  _support_disable_automate_dns_zone = True
  _support_regional_tcp_proxy = True
  _support_ip_collection = True


Create.detailed_help = {
    'DESCRIPTION': ("""
*{{command}}* is used to create a forwarding rule. {overview}

When creating a forwarding rule, exactly one of  ``--target-instance'',
``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
``--target-grpc-proxy'', ``--target-ssl-proxy'', ``--target-tcp-proxy'',
``--target-vpn-gateway'', ``--backend-service'' or ``--target-google-apis-bundle''
must be specified.""".format(overview=flags.FORWARDING_RULES_OVERVIEW)),
    'EXAMPLES':
        """
    To create a global forwarding rule that will forward all traffic on port
    8080 for IP address ADDRESS to a target http proxy PROXY, run:

      $ {command} RULE_NAME --global --target-http-proxy=PROXY --ports=8080 --address=ADDRESS

    To create a regional forwarding rule for the subnet SUBNET_NAME on the
    default network that will forward all traffic on ports 80-82 to a
    backend service SERVICE_NAME, run:

      $ {command} RULE_NAME --load-balancing-scheme=INTERNAL --backend-service=SERVICE_NAME --subnet=SUBNET_NAME --network=default --region=REGION --ports=80-82
"""
}

CreateBeta.detailed_help = Create.detailed_help
CreateAlpha.detailed_help = CreateBeta.detailed_help


def _UnifyPortRangeFromListOfRanges(ports_range_list):
  """Return a single port range by combining a list of port ranges."""
  if not ports_range_list:
    return None, None
  ports = sorted(ports_range_list)
  combined_port_range = ports.pop(0)
  for port_range in ports_range_list:
    try:
      combined_port_range = combined_port_range.Combine(port_range)
    except arg_parsers.Error:
      raise exceptions.InvalidArgumentException(
          '--ports', 'Must specify consecutive ports at this time.')
  return combined_port_range


def _ExtractPortsAndAll(ports_with_all):
  if ports_with_all:
    return ports_with_all.all_specified, ports_with_all.ranges
  else:
    return False, []


def _MakeSingleUnifiedPortRange(arg_port_range, range_list_from_arg_ports):
  """Reconciles the deprecated --port-range arg with ranges from --ports arg."""
  if arg_port_range:
    log.warning(
        'The --port-range flag is deprecated. Use equivalent --ports=%s'
        ' flag.', arg_port_range)
    return six.text_type(arg_port_range)
  elif range_list_from_arg_ports:
    range_list = _UnifyPortRangeFromListOfRanges(range_list_from_arg_ports)
    return six.text_type(range_list) if range_list else None


def _GetPortList(range_list):
  """Creates list of singleton port numbers from list of ports and ranges."""
  ports = []
  for port_range in range_list:
    ports.extend(list(range(port_range.start, port_range.end + 1)))
  return sorted(ports)


def _GetLoadBalancingScheme(args, messages, is_psc):
  """Get load balancing scheme."""
  if not args.load_balancing_scheme:
    # The default is EXTERNAL for non-PSC forwarding rules.
    return None if is_psc else messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.EXTERNAL
  if args.load_balancing_scheme == 'INTERNAL':
    return messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
  elif args.load_balancing_scheme == 'EXTERNAL':
    return messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.EXTERNAL
  elif args.load_balancing_scheme == 'EXTERNAL_MANAGED':
    return messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.EXTERNAL_MANAGED
  elif args.load_balancing_scheme == 'INTERNAL_SELF_MANAGED':
    return (messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum
            .INTERNAL_SELF_MANAGED)
  elif args.load_balancing_scheme == 'INTERNAL_MANAGED':
    return (messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum
            .INTERNAL_MANAGED)
  return None


def _ConstructNetworkTier(messages, args):
  """Get network tier."""
  if args.network_tier:
    network_tier = args.network_tier.upper()
    if network_tier in constants.NETWORK_TIER_CHOICES_FOR_INSTANCE:
      return messages.ForwardingRule.NetworkTierValueValuesEnum(
          args.network_tier)
    else:
      raise exceptions.InvalidArgumentException(
          '--network-tier',
          'Invalid network tier [{tier}]'.format(tier=network_tier))
  else:
    return
