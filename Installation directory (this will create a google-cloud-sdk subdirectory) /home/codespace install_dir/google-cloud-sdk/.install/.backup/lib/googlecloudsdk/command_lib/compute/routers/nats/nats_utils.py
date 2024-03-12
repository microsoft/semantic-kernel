# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple NAT subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.networks.subnets import flags as subnet_flags
from googlecloudsdk.command_lib.compute.routers.nats import flags as nat_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
import six


class NatNotFoundError(core_exceptions.Error):
  """Raised when a NAT is not found."""

  def __init__(self, name):
    self.name = name
    msg = 'NAT `{0}` not found'.format(name)
    super(NatNotFoundError, self).__init__(msg)


class IpAllocateOptionShouldNotBeSpecifiedError(core_exceptions.Error):
  """Raised when IP Allocation option is specified for private NAT."""

  def __init__(self):
    msg = ('--nat-external-ip-pool and --auto-allocate-nat-external-ips '
           'cannot be specified for Private NAT.')
    super(IpAllocateOptionShouldNotBeSpecifiedError, self).__init__(msg)


class IpAllocationUnspecifiedError(core_exceptions.Error):
  """Raised when IP Allocation option is not specified for public NAT."""

  def __init__(self):
    msg = ('Either --nat-external-ip-pool or --auto-allocate-nat-external-ips '
           'must be specified for Public NAT.')
    super(IpAllocationUnspecifiedError, self).__init__(msg)


def FindNatOrRaise(router, nat_name):
  """Returns the nat with the given name in the given router."""
  for nat in router.nats:
    if nat_name == nat.name:
      return nat
  raise NatNotFoundError(nat_name)


def CreateNatMessage(args, compute_holder):
  """Creates a NAT message from the specified arguments."""
  params = {'name': args.name}

  params['sourceSubnetworkIpRangesToNat'], params['subnetworks'] = (
      _ParseSubnetFields(args, compute_holder)
  )

  if args.type is not None:
    params['type'] = (
        compute_holder.client.messages.RouterNat.TypeValueValuesEnum(args.type))

  is_private = args.type == 'PRIVATE'
  is_ip_allocation_specified = (
      args.auto_allocate_nat_external_ips or args.nat_external_ip_pool)
  if is_private:
    if is_ip_allocation_specified:
      raise IpAllocateOptionShouldNotBeSpecifiedError()
  else:
    if not is_ip_allocation_specified:
      raise IpAllocationUnspecifiedError()
    option, nat_ips = _ParseNatIpFields(args, compute_holder)
    params['natIpAllocateOption'] = option
    params['natIps'] = nat_ips

  if args.auto_network_tier is not None:
    params['autoNetworkTier'] = (
        compute_holder.client.messages.RouterNat.AutoNetworkTierValueValuesEnum(
            args.auto_network_tier))

  if args.endpoint_types is not None:
    params['endpointTypes'] = [
        compute_holder.client.messages.RouterNat.EndpointTypesValueListEntryValuesEnum(
            endpoint_type
        )
        for endpoint_type in args.endpoint_types
    ]

  params['udpIdleTimeoutSec'] = args.udp_idle_timeout
  params['icmpIdleTimeoutSec'] = args.icmp_idle_timeout
  params['tcpEstablishedIdleTimeoutSec'] = args.tcp_established_idle_timeout
  params['tcpTransitoryIdleTimeoutSec'] = args.tcp_transitory_idle_timeout
  params['tcpTimeWaitTimeoutSec'] = args.tcp_time_wait_timeout
  params['minPortsPerVm'] = args.min_ports_per_vm
  params['maxPortsPerVm'] = args.max_ports_per_vm
  params['enableDynamicPortAllocation'] = args.enable_dynamic_port_allocation

  if args.enable_logging is not None or args.log_filter is not None:
    log_config = compute_holder.client.messages.RouterNatLogConfig()

    log_config.enable = args.enable_logging
    if args.log_filter is not None:
      log_config.filter = _TranslateLogFilter(args.log_filter, compute_holder)

    params['logConfig'] = log_config

  if args.enable_endpoint_independent_mapping is not None:
    params['enableEndpointIndependentMapping'] = (
        args.enable_endpoint_independent_mapping)

  if args.rules:
    params['rules'] = _ParseRulesFromYamlFile(args.rules, compute_holder)

  return compute_holder.client.messages.RouterNat(**params)


def UpdateNatMessage(nat, args, compute_holder):
  """Updates a NAT message with the specified arguments."""
  if (args.subnet_option in [
      nat_flags.SubnetOption.ALL_RANGES, nat_flags.SubnetOption.PRIMARY_RANGES
  ] or args.nat_custom_subnet_ip_ranges):
    ranges_to_nat, subnetworks = _ParseSubnetFields(args, compute_holder)
    nat.sourceSubnetworkIpRangesToNat = ranges_to_nat
    nat.subnetworks = subnetworks

  if args.nat_external_drain_ip_pool:
    drain_nat_ips = nat_flags.DRAIN_NAT_IP_ADDRESSES_ARG.ResolveAsResource(
        args, compute_holder.resources)
    nat.drainNatIps = [six.text_type(ip) for ip in drain_nat_ips]

    # Remove a IP from nat_ips if it is going to be drained.
    if not args.nat_external_ip_pool:
      nat.natIps = [
          ip for ip in nat.natIps if not _ContainIp(drain_nat_ips, ip)
      ]

  if args.clear_nat_external_drain_ip_pool:
    nat.drainNatIps = []

  if args.auto_allocate_nat_external_ips or args.nat_external_ip_pool:
    option, nat_ips = _ParseNatIpFields(args, compute_holder)
    nat.natIpAllocateOption = option
    nat.natIps = nat_ips

  if args.auto_network_tier is not None:
    nat.autoNetworkTier = (
        compute_holder.client.messages.RouterNat.AutoNetworkTierValueValuesEnum(
            args.auto_network_tier))

  if args.udp_idle_timeout is not None:
    nat.udpIdleTimeoutSec = args.udp_idle_timeout
  elif args.clear_udp_idle_timeout:
    nat.udpIdleTimeoutSec = None

  if args.icmp_idle_timeout is not None:
    nat.icmpIdleTimeoutSec = args.icmp_idle_timeout
  elif args.clear_icmp_idle_timeout:
    nat.icmpIdleTimeoutSec = None

  if args.tcp_established_idle_timeout is not None:
    nat.tcpEstablishedIdleTimeoutSec = args.tcp_established_idle_timeout
  elif args.clear_tcp_established_idle_timeout:
    nat.tcpEstablishedIdleTimeoutSec = None

  if args.tcp_transitory_idle_timeout is not None:
    nat.tcpTransitoryIdleTimeoutSec = args.tcp_transitory_idle_timeout
  elif args.clear_tcp_transitory_idle_timeout:
    nat.tcpTransitoryIdleTimeoutSec = None

  if args.tcp_time_wait_timeout is not None:
    nat.tcpTimeWaitTimeoutSec = args.tcp_time_wait_timeout
  elif args.clear_tcp_time_wait_timeout:
    nat.tcpTimeWaitTimeoutSec = None

  if args.min_ports_per_vm is not None:
    nat.minPortsPerVm = args.min_ports_per_vm
  elif args.clear_min_ports_per_vm:
    nat.minPortsPerVm = None

  if args.max_ports_per_vm is not None:
    nat.maxPortsPerVm = args.max_ports_per_vm
  elif args.clear_max_ports_per_vm:
    nat.maxPortsPerVm = None

  if args.enable_dynamic_port_allocation is not None:
    nat.enableDynamicPortAllocation = args.enable_dynamic_port_allocation

  if args.enable_logging is not None or args.log_filter is not None:
    nat.logConfig = (
        nat.logConfig or compute_holder.client.messages.RouterNatLogConfig())
  if args.enable_logging is not None:
    nat.logConfig.enable = args.enable_logging
  if args.log_filter is not None:
    nat.logConfig.filter = _TranslateLogFilter(args.log_filter, compute_holder)

  if args.enable_endpoint_independent_mapping is not None:
    nat.enableEndpointIndependentMapping = (
        args.enable_endpoint_independent_mapping)

  if args.rules:
    nat.rules = _ParseRulesFromYamlFile(args.rules, compute_holder)

  return nat


class SubnetUsage(object):
  """Helper object to store what ranges of a subnetwork are used for NAT."""

  def __init__(self):
    self.using_primary = False
    self.using_all = False
    self.secondary_ranges = list()


def _ParseSubnetFields(args, compute_holder):
  """Parses arguments related to subnets to use for NAT."""
  subnetworks = list()
  messages = compute_holder.client.messages
  if args.subnet_option == nat_flags.SubnetOption.ALL_RANGES:
    ranges_to_nat = (
        messages.RouterNat.SourceSubnetworkIpRangesToNatValueValuesEnum
        .ALL_SUBNETWORKS_ALL_IP_RANGES)
  elif args.subnet_option == nat_flags.SubnetOption.PRIMARY_RANGES:
    ranges_to_nat = (
        messages.RouterNat.SourceSubnetworkIpRangesToNatValueValuesEnum
        .ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES)
  else:
    ranges_to_nat = (
        messages.RouterNat.SourceSubnetworkIpRangesToNatValueValuesEnum
        .LIST_OF_SUBNETWORKS)

    # Mapping of subnet names to SubnetUsage.
    subnet_usages = dict()

    for custom_subnet_arg in args.nat_custom_subnet_ip_ranges:
      colons = custom_subnet_arg.count(':')
      range_option = None
      if colons > 1:
        raise calliope_exceptions.InvalidArgumentException(
            '--nat-custom-subnet-ip-ranges',
            ('Each specified subnet must be of the form SUBNETWORK '
             'or SUBNETWORK:RANGE_NAME'))
      elif colons == 1:
        subnet_name, range_option = custom_subnet_arg.split(':')
      else:
        subnet_name = custom_subnet_arg

      if subnet_name not in subnet_usages:
        subnet_usages[subnet_name] = SubnetUsage()

      if range_option is not None:
        if range_option == 'ALL':
          subnet_usages[subnet_name].using_all = True
        else:
          subnet_usages[subnet_name].secondary_ranges.append(range_option)
      else:
        subnet_usages[subnet_name].using_primary = True

    for subnet_name in subnet_usages:
      subnet_ref = subnet_flags.SubnetworkResolver().ResolveResources(
          [subnet_name],
          compute_scope.ScopeEnum.REGION,
          args.region,
          compute_holder.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(
              compute_holder.client))

      subnet_usage = subnet_usages[subnet_name]

      options = []
      if subnet_usage.using_all:
        options.append(
            messages.RouterNatSubnetworkToNat
            .SourceIpRangesToNatValueListEntryValuesEnum.ALL_IP_RANGES)
      if subnet_usage.using_primary:
        options.append(
            messages.RouterNatSubnetworkToNat
            .SourceIpRangesToNatValueListEntryValuesEnum.PRIMARY_IP_RANGE)
      if subnet_usage.secondary_ranges:
        options.append(messages.RouterNatSubnetworkToNat
                       .SourceIpRangesToNatValueListEntryValuesEnum
                       .LIST_OF_SECONDARY_IP_RANGES)

      subnetworks.append({
          'name': six.text_type(subnet_ref[0]),
          'sourceIpRangesToNat': options,
          'secondaryIpRangeNames': subnet_usage.secondary_ranges
      })
  # Sorted for test stability.
  return (ranges_to_nat, sorted(subnetworks, key=lambda subnet: subnet['name']))


def _ParseNatIpFields(args, compute_holder):
  messages = compute_holder.client.messages
  if args.auto_allocate_nat_external_ips:
    return (messages.RouterNat.NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            list())
  return (messages.RouterNat.NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY, [
      six.text_type(address)
      for address in nat_flags.IP_ADDRESSES_ARG.ResolveAsResource(
          args, compute_holder.resources)
  ])


def _TranslateLogFilter(filter_str, compute_holder):
  """Translates the specified log filter to the enum value."""
  if filter_str == 'ALL':
    return (compute_holder.client.messages.RouterNatLogConfig
            .FilterValueValuesEnum.ALL)
  if filter_str == 'TRANSLATIONS_ONLY':
    return (compute_holder.client.messages.RouterNatLogConfig
            .FilterValueValuesEnum.TRANSLATIONS_ONLY)
  if filter_str == 'ERRORS_ONLY':
    return (compute_holder.client.messages.RouterNatLogConfig
            .FilterValueValuesEnum.ERRORS_ONLY)

  raise calliope_exceptions.InvalidArgumentException(
      '--log-filter', ('--log-filter must be ALL, TRANSLATIONS_ONLY '
                       'or ERRORS_ONLY'))


def _ContainIp(ip_list, target_ip):
  """Returns true if target ip is in the list."""
  for ip in ip_list:
    if ip.RelativeName() in target_ip:
      return True
  return False


def _ParseRulesFromYamlFile(file_path, compute_holder):
  """Parses NAT Rules from the given YAML file."""
  with files.FileReader(file_path) as import_file:
    rules_yaml = yaml.load(import_file)
    if 'rules' not in rules_yaml:
      raise calliope_exceptions.InvalidArgumentException(
          '--rules', 'The YAML file must contain the \'rules\' attribute')
    return [
        _CreateRule(rule_yaml, compute_holder)
        for rule_yaml in rules_yaml['rules']
    ]


def _CreateRule(rule_yaml, compute_holder):
  """Creates a Rule object from the given parsed YAML."""
  rule = compute_holder.client.messages.RouterNatRule()
  if 'ruleNumber' in rule_yaml:
    rule.ruleNumber = rule_yaml['ruleNumber']
  if 'match' in rule_yaml:
    rule.match = rule_yaml['match']
  if 'action' in rule_yaml:
    action_yaml = rule_yaml['action']
    rule.action = compute_holder.client.messages.RouterNatRuleAction()
    if 'sourceNatActiveIps' in action_yaml:
      rule.action.sourceNatActiveIps = action_yaml['sourceNatActiveIps']
    if 'sourceNatDrainIps' in action_yaml:
      rule.action.sourceNatDrainIps = action_yaml['sourceNatDrainIps']
    if 'sourceNatActiveRanges' in action_yaml:
      rule.action.sourceNatActiveRanges = action_yaml['sourceNatActiveRanges']
    if 'sourceNatDrainRanges' in action_yaml:
      rule.action.sourceNatDrainRanges = action_yaml['sourceNatDrainRanges']

  return rule
