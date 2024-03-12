# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for creating packet mirroring resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.packet_mirrorings import client
from googlecloudsdk.command_lib.compute.packet_mirrorings import flags
from googlecloudsdk.command_lib.compute.packet_mirrorings import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine packet mirroring policy."""

  PACKET_MIRRORING_ARG = None

  @classmethod
  def Args(cls, parser):
    base.ASYNC_FLAG.AddToParser(parser)

    cls.PACKET_MIRRORING_ARG = flags.PacketMirroringArgument()
    cls.PACKET_MIRRORING_ARG.AddArgument(parser, operation_type='create')

    flags.AddCreateArgs(parser)

  def Collection(self):
    return 'compute.packetMirrorings'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages

    pm_ref = self.PACKET_MIRRORING_ARG.ResolveAsResource(args, holder.resources)

    def _MakeInstanceInfo(instance):
      return messages.PacketMirroringMirroredResourceInfoInstanceInfo(
          url=utils.ResolveInstanceURI(pm_ref.project, instance,
                                       holder.resources))

    def _MakeMirroredSubnetInfo(subnet):
      return messages.PacketMirroringMirroredResourceInfoSubnetInfo(
          url=utils.ResolveSubnetURI(pm_ref.project, pm_ref.region, subnet,
                                     holder.resources))

    mirrored_instance_infos = [
        _MakeInstanceInfo(instance) for instance in args.mirrored_instances
    ] if args.mirrored_instances else []

    mirrored_subnet_infos = [
        _MakeMirroredSubnetInfo(subnet) for subnet in args.mirrored_subnets
    ] if args.mirrored_subnets else []

    pm_filter = messages.PacketMirroringFilter()
    if args.filter_cidr_ranges or args.filter_protocols:
      if args.filter_cidr_ranges:
        pm_filter.cidrRanges.extend(args.filter_cidr_ranges)
      if args.filter_protocols:
        pm_filter.IPProtocols.extend(args.filter_protocols)

    if args.filter_direction:
      pm_filter.direction = messages.PacketMirroringFilter.DirectionValueValuesEnum(
          args.filter_direction.upper())

    mirrored_resources_info = messages.PacketMirroringMirroredResourceInfo(
        subnetworks=mirrored_subnet_infos,
        instances=mirrored_instance_infos,
        tags=args.mirrored_tags or [])
    template = messages.PacketMirroring(
        name=pm_ref.Name(),
        description=args.description,
        network=messages.PacketMirroringNetworkInfo(
            url=utils.ResolveNetworkURI(pm_ref.project, args.network,
                                        holder.resources)),
        collectorIlb=messages.PacketMirroringForwardingRuleInfo(
            url=utils.ResolveForwardingRuleURI(pm_ref.project, pm_ref.region,
                                               args.collector_ilb,
                                               holder.resources)),
        mirroredResources=mirrored_resources_info,
        filter=pm_filter,
        enable=messages.PacketMirroring.EnableValueValuesEnum.TRUE if
        args.enable else messages.PacketMirroring.EnableValueValuesEnum.FALSE)

    packet_mirroring = client.PacketMirroring(
        pm_ref, compute_client=holder.client, registry=holder.resources)

    return packet_mirroring.Create(template, is_async=args.async_ or False)

Create.detailed_help = {
    'DESCRIPTION': 'Create a Compute Engine packet mirroring policy.',
    'EXAMPLES':
    """\
    Mirror all tcp traffic to/from all instances in subnet my-subnet in
    us-central1, and send the mirrored traffic to the collector-fr
    Forwarding Rule.

      $ {command} my-pm
        --network my-network --region us-central1
        --mirrored-subnets my-subnet --collector-ilb collector-fr
        --filter-protocols tcp

    Mirror all traffic between instances with tag t1 and external server with IP
    11.22.33.44 in us-central1, and send the mirrored traffic to the
    collector-fr Forwarding Rule.

      $ {command} my-pm
        --network my-network --region us-central1
        --mirrored-tags t1 --collector-ilb collector-fr
        --filter-cidr-ranges 11.22.33.44/32
    """,
}
