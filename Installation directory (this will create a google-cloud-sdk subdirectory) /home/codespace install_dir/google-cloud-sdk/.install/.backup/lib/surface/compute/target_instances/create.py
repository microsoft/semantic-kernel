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
"""Command for creating target instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import (flags as
                                                          instance_flags)
from googlecloudsdk.command_lib.compute.target_instances import flags


class CreateHelper(object):
  """Helper class to creat a target instance."""

  INSTANCE_ARG = None
  TARGET_INSTANCE_ARG = None

  @classmethod
  def Args(cls, parser):
    """Add flags to create a target instance to the parser."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.INSTANCE_ARG = instance_flags.InstanceArgumentForTargetInstance()
    cls.INSTANCE_ARG.AddArgument(parser)
    cls.TARGET_INSTANCE_ARG = flags.TargetInstanceArgument()
    cls.TARGET_INSTANCE_ARG.AddArgument(parser)

    flags.AddNetwork(parser)

    parser.add_argument(
        '--description',
        help='An optional, textual description of the target instance.')

    parser.display_info.AddCacheUpdater(flags.TargetInstancesCompleter)

  def __init__(self):
    pass

  def Run(self, args, holder):
    """Issues request necessary to create a target instance."""
    client = holder.client

    target_instance_ref = self.TARGET_INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if target_instance_ref.zone and not args.instance_zone:
      args.instance_zone = target_instance_ref.zone

    instance_ref = self.INSTANCE_ARG.ResolveAsResource(args, holder.resources)

    if target_instance_ref.zone != instance_ref.zone:
      raise compute_exceptions.ArgumentError(
          'Target instance zone must match the virtual machine instance zone.')

    target_instance = client.messages.TargetInstance(
        description=args.description,
        name=target_instance_ref.Name(),
        instance=instance_ref.SelfLink())

    if args.IsSpecified('network'):
      target_instance.network = flags.NETWORK_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()

    request = client.messages.ComputeTargetInstancesInsertRequest(
        targetInstance=target_instance,
        project=target_instance_ref.project,
        zone=target_instance_ref.zone)

    return client.MakeRequests([(client.apitools_client.targetInstances,
                                 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a target instance for handling traffic from a forwarding rule.

    *{command}* is used to create a target instance for handling
  traffic from one or more forwarding rules. Target instances
  are ideal for traffic that should be managed by a single
  source. For more information on target instances, see
  [](https://cloud.google.com/compute/docs/protocol-forwarding/#targetinstances)
  """

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return CreateHelper().Run(args, holder)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create a target instance for handling traffic from a forwarding rule.

    *{command}* is used to create a target instance for handling
  traffic from one or more forwarding rules. Target instances
  are ideal for traffic that should be managed by a single
  source. For more information on target instances, see
  [](https://cloud.google.com/compute/docs/protocol-forwarding/#targetinstances)
  """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a target instance for handling traffic from a forwarding rule.

    *{command}* is used to create a target instance for handling
  traffic from one or more forwarding rules. Target instances
  are ideal for traffic that should be managed by a single
  source. For more information on target instances, see
  [](https://cloud.google.com/compute/docs/protocol-forwarding/#targetinstances)
  """
