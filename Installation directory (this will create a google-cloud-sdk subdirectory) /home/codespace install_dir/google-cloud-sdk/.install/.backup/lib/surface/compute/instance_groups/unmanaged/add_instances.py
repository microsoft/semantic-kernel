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
"""Command for adding instances to unmanaged instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


class AddInstances(base.SilentCommand):
  r"""Adds instances to an unmanaged instance group by name.

    *{command}* adds existing instances to an unmanaged instance group
  by name.
  For example:

    $ {command} my-group \
        --instances my-instance-1,my-instance-2 --zone us-central1-a
  """

  ZONAL_INSTANCE_GROUP_ARG = None

  @staticmethod
  def Args(parser):
    AddInstances.ZONAL_INSTANCE_GROUP_ARG = (
        instance_groups_flags.MakeZonalInstanceGroupArg())
    AddInstances.ZONAL_INSTANCE_GROUP_ARG.AddArgument(parser)
    parser.add_argument(
        '--instances',
        required=True,
        type=arg_parsers.ArgList(min_length=1),
        metavar='INSTANCE',
        help='A list of names of instances to add to the instance group. '
        'These must exist beforehand and must live in the same zone as '
        'the instance group.')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = (
        AddInstances.ZONAL_INSTANCE_GROUP_ARG.ResolveAsResource(
            args, holder.resources,
            default_scope=None,
            scope_lister=flags.GetDefaultScopeLister(client)))

    instance_references = []
    for instance in args.instances:
      ref = holder.resources.Parse(
          instance,
          params={
              'project': group_ref.project,
              'zone': group_ref.zone
          },
          collection='compute.instances')
      instance_references.append(ref)

    instance_groups_utils.ValidateInstanceInZone(instance_references,
                                                 group_ref.zone)
    instance_references = [
        client.messages.InstanceReference(instance=inst.SelfLink())
        for inst in instance_references]
    request_payload = client.messages.InstanceGroupsAddInstancesRequest(
        instances=instance_references)

    request = client.messages.ComputeInstanceGroupsAddInstancesRequest(
        instanceGroup=group_ref.Name(),
        instanceGroupsAddInstancesRequest=request_payload,
        zone=group_ref.zone,
        project=group_ref.project
    )

    return client.MakeRequests(
        [(client.apitools_client.instanceGroups, 'AddInstances', request)]
    )
