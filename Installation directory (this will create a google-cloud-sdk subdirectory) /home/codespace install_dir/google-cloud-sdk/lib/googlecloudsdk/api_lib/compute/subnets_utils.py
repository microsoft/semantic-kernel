# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple subnets subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.networks.subnets import flags
import six


def _CreateSecondaryRange(client, name, ip_cidr_range, reserved_internal_range):
  """Creates a subnetwork secondary range."""
  if reserved_internal_range and ip_cidr_range:
    return client.messages.SubnetworkSecondaryRange(
        rangeName=name,
        reservedInternalRange=reserved_internal_range,
        ipCidrRange=ip_cidr_range)
  elif reserved_internal_range:
    return client.messages.SubnetworkSecondaryRange(
        rangeName=name, reservedInternalRange=reserved_internal_range)
  else:
    return client.messages.SubnetworkSecondaryRange(
        rangeName=name, ipCidrRange=ip_cidr_range)


def CreateSecondaryRanges(client, secondary_range,
                          secondary_range_with_reserved_internal_range):
  """Creates all secondary ranges of a subnet."""
  secondary_ranges = []
  range_name_to_cidr = {}
  range_name_to_reserved_internal_range = {}
  range_names = set()
  if secondary_range:
    for secondary_range in secondary_range:
      for range_name, ip_cidr_range in six.iteritems(secondary_range):
        range_name_to_cidr[range_name] = ip_cidr_range
        range_names.add(range_name)
  if secondary_range_with_reserved_internal_range:
    for secondary_range in secondary_range_with_reserved_internal_range:
      for range_name, internal_range in six.iteritems(secondary_range):
        range_name_to_reserved_internal_range[range_name] = internal_range
        range_names.add(range_name)
  for range_name in sorted(range_names):
    secondary_ranges.append(
        _CreateSecondaryRange(
            client, range_name, range_name_to_cidr.get(range_name),
            range_name_to_reserved_internal_range.get(range_name)))
  return secondary_ranges


def MakeSubnetworkUpdateRequest(
    client,
    subnet_ref,
    enable_private_ip_google_access=None,
    allow_cidr_routes_overlap=None,
    add_secondary_ranges=None,
    add_secondary_ranges_with_reserved_internal_range=None,
    remove_secondary_ranges=None,
    enable_flow_logs=None,
    aggregation_interval=None,
    flow_sampling=None,
    metadata=None,
    filter_expr=None,
    metadata_fields=None,
    set_new_purpose=None,
    set_role_active=None,
    drain_timeout_seconds=None,
    private_ipv6_google_access_type=None,
    stack_type=None,
    ipv6_access_type=None,
    external_ipv6_prefix=None,
):
  """Make the appropriate update request for the args.

  Args:
    client: GCE API client
    subnet_ref: Reference to a subnetwork
    enable_private_ip_google_access: Enable/disable access to Google Cloud APIs
      from this subnet for instances without a public ip address.
    allow_cidr_routes_overlap: Allow/Disallow this subnetwork's ranges to
      conflict with existing static routes.
    add_secondary_ranges: List of secondary IP ranges to add to the subnetwork
      for use in IP aliasing.
    add_secondary_ranges_with_reserved_internal_range: List of secondary IP
      ranges that are associated with InternalRange resources.
    remove_secondary_ranges: List of secondary ranges to remove from the
      subnetwork.
    enable_flow_logs: Enable/disable flow logging for this subnet.
    aggregation_interval: The internal at which to aggregate flow logs.
    flow_sampling: The sampling rate for flow logging in this subnet.
    metadata: Whether metadata fields should be added reported flow logs.
    filter_expr: custom CEL expression for filtering flow logs
    metadata_fields: custom metadata fields to be added to flow logs
    set_new_purpose: Update the purpose of the subnet.
    set_role_active: Updates the role of a BACKUP subnet to ACTIVE.
    drain_timeout_seconds: The maximum amount of time to drain connections from
      the active subnet to the backup subnet with set_role_active=True.
    private_ipv6_google_access_type: The private IPv6 google access type for the
      VMs in this subnet.
    stack_type: The stack type for this subnet.
    ipv6_access_type: The IPv6 access type for this subnet.
    external_ipv6_prefix: The IPv6 external prefix to be assigned to this
      subnet.

  Returns:
    response, result of sending the update request for the subnetwork
  """
  convert_to_enum = lambda x: x.replace('-', '_').upper()
  if enable_private_ip_google_access is not None:
    google_access = (
        client.messages.SubnetworksSetPrivateIpGoogleAccessRequest())
    google_access.privateIpGoogleAccess = enable_private_ip_google_access

    google_access_request = (
        client.messages.ComputeSubnetworksSetPrivateIpGoogleAccessRequest(
            project=subnet_ref.project,
            region=subnet_ref.region,
            subnetwork=subnet_ref.Name(),
            subnetworksSetPrivateIpGoogleAccessRequest=google_access))
    return client.MakeRequests([
        (client.apitools_client.subnetworks, 'SetPrivateIpGoogleAccess',
         google_access_request)
    ])
  elif (add_secondary_ranges is not None or
        add_secondary_ranges_with_reserved_internal_range is not None):
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.secondaryIpRanges = original_subnetwork.secondaryIpRanges
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.secondaryIpRanges.extend(
        CreateSecondaryRanges(
            client, add_secondary_ranges,
            add_secondary_ranges_with_reserved_internal_range))

    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif remove_secondary_ranges is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.secondaryIpRanges = original_subnetwork.secondaryIpRanges
    subnetwork.fingerprint = original_subnetwork.fingerprint

    for name in remove_secondary_ranges[0]:
      if name not in [r.rangeName for r in subnetwork.secondaryIpRanges]:
        raise calliope_exceptions.UnknownArgumentException(
            'remove-secondary-ranges', 'Subnetwork does not have a range {}, '
            'present ranges are {}.'.format(
                name, [r.rangeName for r in subnetwork.secondaryIpRanges]))
    subnetwork.secondaryIpRanges = [
        r for r in original_subnetwork.secondaryIpRanges
        if r.rangeName not in remove_secondary_ranges[0]
    ]

    cleared_fields = []
    if not subnetwork.secondaryIpRanges:
      cleared_fields.append('secondaryIpRanges')
    with client.apitools_client.IncludeFields(cleared_fields):
      return client.MakeRequests(
          [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif (enable_flow_logs is not None or aggregation_interval is not None or
        flow_sampling is not None or metadata is not None or
        filter_expr is not None or metadata_fields is not None):
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    log_config = client.messages.SubnetworkLogConfig(enable=enable_flow_logs)
    if aggregation_interval is not None:
      log_config.aggregationInterval = flags.GetLoggingAggregationIntervalArg(
          client.messages).GetEnumForChoice(aggregation_interval)
    if flow_sampling is not None:
      log_config.flowSampling = flow_sampling
    if metadata is not None:
      log_config.metadata = flags.GetLoggingMetadataArg(
          client.messages).GetEnumForChoice(metadata)
    if filter_expr is not None:
      log_config.filterExpr = filter_expr
    if metadata_fields is not None:
      log_config.metadataFields = metadata_fields
    subnetwork.logConfig = log_config

    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif private_ipv6_google_access_type is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.privateIpv6GoogleAccess = (
        client.messages.Subnetwork.PrivateIpv6GoogleAccessValueValuesEnum(
            ConvertPrivateIpv6GoogleAccess(
                convert_to_enum(private_ipv6_google_access_type))))
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif allow_cidr_routes_overlap is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([(
        client.apitools_client.subnetworks,
        'Get',
        client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()),
    )])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.allowSubnetCidrRoutesOverlap = allow_cidr_routes_overlap
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)]
    )
  elif set_new_purpose is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.purpose = client.messages.Subnetwork.PurposeValueValuesEnum(
        set_new_purpose)
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif set_role_active is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.role = client.messages.Subnetwork.RoleValueValuesEnum.ACTIVE
    patch_request = client.messages.ComputeSubnetworksPatchRequest(
        project=subnet_ref.project,
        subnetwork=subnet_ref.subnetwork,
        region=subnet_ref.region,
        subnetworkResource=subnetwork,
        drainTimeoutSeconds=drain_timeout_seconds)
    return client.MakeRequests([(client.apitools_client.subnetworks, 'Patch',
                                 patch_request)])
  elif stack_type is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.stackType = (
        client.messages.Subnetwork.StackTypeValueValuesEnum(stack_type))
    if ipv6_access_type is not None:
      subnetwork.ipv6AccessType = (
          client.messages.Subnetwork.Ipv6AccessTypeValueValuesEnum(
              ipv6_access_type))
    if external_ipv6_prefix is not None:
      subnetwork.externalIpv6Prefix = external_ipv6_prefix
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])

  return client.MakeRequests([])


def CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork_resource):
  patch_request = client.messages.ComputeSubnetworksPatchRequest(
      project=subnet_ref.project,
      subnetwork=subnet_ref.subnetwork,
      region=subnet_ref.region,
      subnetworkResource=subnetwork_resource)
  return (client.apitools_client.subnetworks, 'Patch', patch_request)


def ConvertPrivateIpv6GoogleAccess(choice):
  """Return PrivateIpv6GoogleAccess enum defined in mixer.

  Args:
    choice: Enum value of PrivateIpv6GoogleAccess defined in gcloud.
  """
  choices_to_enum = {
      'DISABLE': 'DISABLE_GOOGLE_ACCESS',
      'ENABLE_BIDIRECTIONAL_ACCESS': 'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE',
      'ENABLE_OUTBOUND_VM_ACCESS': 'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE',
  }
  return choices_to_enum.get(choice)
