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
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.packet_mirrorings import client
from googlecloudsdk.command_lib.compute.packet_mirrorings import flags
from googlecloudsdk.command_lib.compute.packet_mirrorings import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Compute Engine packet mirroring policy."""

  PACKET_MIRRORING_ARG = None

  @classmethod
  def Args(cls, parser):
    base.ASYNC_FLAG.AddToParser(parser)

    cls.PACKET_MIRRORING_ARG = flags.PacketMirroringArgument()
    cls.PACKET_MIRRORING_ARG.AddArgument(parser, operation_type='update')

    flags.AddUpdateArgs(parser)

  def Collection(self):
    return 'compute.packetMirrorings'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages

    pm_ref = self.PACKET_MIRRORING_ARG.ResolveAsResource(args, holder.resources)

    packet_mirroring = client.PacketMirroring(
        pm_ref, compute_client=holder.client, registry=holder.resources)

    resource = packet_mirroring.Describe()[0]
    cleared_fields = []
    self._UpdateResource(pm_ref, resource, cleared_fields, holder, args,
                         messages)

    packet_mirroring.Update(
        resource, is_async=args.async_ or False, cleared_fields=cleared_fields)

  def _UpdateResource(self, pm_ref, resource, cleared_fields, holder, args,
                      messages):
    if args.enable is not None:
      resource.enable = (
          messages.PacketMirroring.EnableValueValuesEnum.TRUE if args.enable
          else messages.PacketMirroring.EnableValueValuesEnum.FALSE)

    if args.collector_ilb is not None:
      resource.collectorIlb = messages.PacketMirroringForwardingRuleInfo(
          url=utils.ResolveForwardingRuleURI(pm_ref.project, pm_ref.region, args
                                             .collector_ilb, holder.resources))

    if args.description is not None:
      resource.description = args.description

    if args.clear_mirrored_tags:
      resource.mirroredResources.tags[:] = []
      cleared_fields.append('mirroredResources.tags')
    elif args.add_mirrored_tags:
      resource.mirroredResources.tags.extend(args.add_mirrored_tags)
    elif args.set_mirrored_tags:
      resource.mirroredResources.tags[:] = args.set_mirrored_tags
    elif args.remove_mirrored_tags:
      for tag in args.remove_mirrored_tags:
        if tag not in resource.mirroredResources.tags:
          raise exceptions.InvalidArgumentException(
              'Tag %s not found in this packet mirroring.' % tag)
      resource.mirroredResources.tags[:] = [
          x for x in resource.mirroredResources.tags
          if x not in args.remove_mirrored_tags
      ]

    def _MakeSubnetInfo(subnet):
      return messages.PacketMirroringMirroredResourceInfoSubnetInfo(
          url=utils.ResolveSubnetURI(pm_ref.project, pm_ref.region, subnet,
                                     holder.resources))

    if args.clear_mirrored_subnets:
      resource.mirroredResources.subnetworks[:] = []
      cleared_fields.append('mirroredResources.subnetworks')
    elif args.add_mirrored_subnets:
      resource.mirroredResources.subnetworks.extend(
          [_MakeSubnetInfo(subnet) for subnet in args.add_mirrored_subnets])
    elif args.set_mirrored_subnets:
      resource.mirroredResources.subnetworks[:] = [
          _MakeSubnetInfo(subnet) for subnet in args.set_mirrored_subnets
      ]
    elif args.remove_mirrored_subnets:
      urls = [
          utils.ResolveSubnetURI(pm_ref.project, pm_ref.region, subnet,
                                 holder.resources)
          for subnet in args.remove_mirrored_subnets
      ]
      for url in urls:
        if next(
            (x for x in resource.mirroredResources.subnetworks if x.url == url),
            None) is None:
          raise exceptions.InvalidArgumentException(
              'Subnet %s not found in this packet mirroring.' % url)
      resource.mirroredResources.subnetworks = [
          x for x in resource.mirroredResources.subnetworks if x.url not in urls
      ]

    def _MakeInstanceInfo(instance):
      return messages.PacketMirroringMirroredResourceInfoInstanceInfo(
          url=utils.ResolveInstanceURI(pm_ref.project, instance,
                                       holder.resources))

    if args.clear_mirrored_instances:
      resource.mirroredResources.instances[:] = []
      cleared_fields.append('mirroredResources.instances')
    elif args.add_mirrored_instances:
      resource.mirroredResources.instances.extend([
          _MakeInstanceInfo(instance)
          for instance in args.add_mirrored_instances
      ])
    elif args.set_mirrored_instances:
      resource.mirroredResources.instances[:] = [
          _MakeInstanceInfo(instance)
          for instance in args.set_mirrored_instances
      ]
    elif args.remove_mirrored_instances:
      urls = [
          utils.ResolveInstanceURI(pm_ref.project, instance, holder.resources)
          for instance in args.remove_mirrored_instances
      ]
      for url in urls:
        if next(
            (x for x in resource.mirroredResources.instances if x.url == url),
            None) is None:
          raise exceptions.InvalidArgumentException(
              'Instance %s not found in this packet mirroring.' % url)
      resource.mirroredResources.instances = [
          x for x in resource.mirroredResources.instances if x.url not in urls
      ]

    if args.clear_filter_protocols:
      resource.filter.IPProtocols[:] = []
    elif args.add_filter_protocols:
      resource.filter.IPProtocols.extend(args.add_filter_protocols)
    elif args.set_filter_protocols:
      resource.filter.IPProtocols[:] = args.set_filter_protocols
    elif args.remove_filter_protocols:
      for protocol in args.remove_filter_protocols:
        if protocol not in resource.filter.IPProtocols:
          raise exceptions.InvalidArgumentException(
              'Protocol %s not found in this packet mirroring.' % protocol)
      resource.filter.IPProtocols[:] = [
          x for x in resource.filter.IPProtocols
          if x not in args.remove_filter_protocols
      ]

    if args.clear_filter_cidr_ranges:
      resource.filter.cidrRanges[:] = []
    elif args.add_filter_cidr_ranges:
      resource.filter.cidrRanges.extend(args.add_filter_cidr_ranges)
    elif args.set_filter_cidr_ranges:
      resource.filter.cidrRanges[:] = args.set_filter_cidr_ranges
    elif args.remove_filter_cidr_ranges:
      for cidr in args.remove_filter_cidr_ranges:
        if cidr not in resource.filter.cidrRanges:
          raise exceptions.InvalidArgumentException(
              'CIDR Range %s not found in this packet mirroring.' % cidr)
      resource.filter.cidrRanges[:] = [
          x for x in resource.filter.cidrRanges
          if x not in args.remove_filter_cidr_ranges
      ]

    if args.filter_direction:
      resource.filter.direction = messages.PacketMirroringFilter.DirectionValueValuesEnum(
          args.filter_direction.upper())


Update.detailed_help = {
    'DESCRIPTION':
        'Update a Compute Engine packet mirroring policy.',
    'EXAMPLES':
        """\
    Stop mirroring by tags, add subnet-1 as a mirrored subnet.

      $ {command} my-pm
          --region us-central1 --clear-mirrored-tags
          --add-mirrored-subnets subnet-1

    Change the load-balancer to send mirrored traffic to.

      $ {command} my-pm
          --region us-central1 --collector-ilb new-forwarding-rule

    Disable a Packet Mirroring policy.

      $ {command} my-pm
          --region us-central1 --no-enable

    Re-enable a disabled Packet Mirroring policy.

      $ {command} my-pm
          --region us-central1 --enable
    """,
}
