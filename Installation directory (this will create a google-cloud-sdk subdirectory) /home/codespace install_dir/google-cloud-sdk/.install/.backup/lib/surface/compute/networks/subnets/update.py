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
"""Command for modifying the properties of a subnetwork."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import subnets_utils
from googlecloudsdk.api_lib.compute import utils as compute_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks.subnets import flags


def _DetailedHelp():
  return {
      'brief':
          'Updates properties of an existing Compute Engine subnetwork.',
      'DESCRIPTION':
          """\
          *{command}* is used to update properties of an existing Compute Engine
          subnetwork.
      """,
      'EXAMPLES':
          """\
        To enable external IPv6 addresses on the subnetwork example-subnet-1 in
        network-1, run

        $ {command} example-subnet-1 --stack-type=IPV4_IPV6 \
--ipv6-access-type=EXTERNAL \
--region=REGION
      """
  }


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Updates properties of an existing Compute Engine subnetwork."""

  _include_alpha_logging = False
  _include_external_ipv6_prefix = False
  _include_allow_cidr_routes_overlap = False
  _api_version = compute_api.COMPUTE_GA_API_VERSION
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    """The command arguments handler.

    Args:
      parser: An argparse.ArgumentParser instance.
    """
    cls.SUBNETWORK_ARG = flags.SubnetworkArgument()
    cls.SUBNETWORK_ARG.AddArgument(parser, operation_type='update')

    flags.AddUpdateArgs(
        parser,
        cls._include_alpha_logging,
        cls._include_external_ipv6_prefix,
        cls._include_allow_cidr_routes_overlap,
        cls._api_version,
    )

  def Run(self, args):
    """Issues requests necessary to update Subnetworks."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    subnet_ref = self.SUBNETWORK_ARG.ResolveAsResource(args, holder.resources)

    aggregation_interval = args.logging_aggregation_interval
    flow_sampling = args.logging_flow_sampling
    metadata = args.logging_metadata
    filter_expr = args.logging_filter_expr
    metadata_fields = args.logging_metadata_fields

    if self._include_alpha_logging:
      if args.aggregation_interval is not None:
        aggregation_interval = args.aggregation_interval
      if args.flow_sampling is not None:
        flow_sampling = args.flow_sampling
      if args.metadata is not None:
        metadata = args.metadata

    set_role_active = None
    drain_timeout_seconds = args.drain_timeout
    if args.role is not None:
      set_role_active = getattr(args, 'role', None) == 'ACTIVE'

    set_new_purpose = None
    if args.purpose is not None:
      set_new_purpose = getattr(args, 'purpose', None)

    private_ipv6_google_access_type = args.private_ipv6_google_access_type

    allow_cidr_routes_overlap = None
    if self._include_allow_cidr_routes_overlap:
      allow_cidr_routes_overlap = args.allow_cidr_routes_overlap

    stack_type = getattr(args, 'stack_type', None)
    ipv6_access_type = getattr(args, 'ipv6_access_type', None)

    reserved_internal_ranges = getattr(
        args, 'add_secondary_ranges_with_reserved_internal_range', None)

    external_ipv6_prefix = getattr(args, 'external_ipv6_prefix', None)

    return subnets_utils.MakeSubnetworkUpdateRequest(
        client,
        subnet_ref,
        enable_private_ip_google_access=args.enable_private_ip_google_access,
        add_secondary_ranges=args.add_secondary_ranges,
        add_secondary_ranges_with_reserved_internal_range=reserved_internal_ranges,
        remove_secondary_ranges=args.remove_secondary_ranges,
        enable_flow_logs=args.enable_flow_logs,
        aggregation_interval=aggregation_interval,
        flow_sampling=flow_sampling,
        metadata=metadata,
        filter_expr=filter_expr,
        metadata_fields=metadata_fields,
        set_role_active=set_role_active,
        set_new_purpose=set_new_purpose,
        drain_timeout_seconds=drain_timeout_seconds,
        private_ipv6_google_access_type=private_ipv6_google_access_type,
        allow_cidr_routes_overlap=allow_cidr_routes_overlap,
        stack_type=stack_type,
        ipv6_access_type=ipv6_access_type,
        external_ipv6_prefix=external_ipv6_prefix,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Updates properties of an existing Compute Engine subnetwork."""

  _include_external_ipv6_prefix = False
  _include_allow_cidr_routes_overlap = True
  _api_version = compute_api.COMPUTE_BETA_API_VERSION


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Updates properties of an existing Compute Engine subnetwork."""

  _include_alpha_logging = True
  _include_external_ipv6_prefix = True
  _include_allow_cidr_routes_overlap = True
  _api_version = compute_api.COMPUTE_ALPHA_API_VERSION
