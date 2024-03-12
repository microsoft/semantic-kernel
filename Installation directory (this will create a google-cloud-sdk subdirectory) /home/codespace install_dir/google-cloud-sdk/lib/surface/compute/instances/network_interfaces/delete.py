# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud command to delete a single NIC from a running VM."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  r"""Delete a Compute Engine virtual machine network interface.

  *{command}* deletes network interface of a Compute Engine
  virtual machine. For example:

    $ {command} instance-name --network-interface nic1.2
  """

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor):
    instances_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--network-interface',
        required=True,
        help='The name of the network interface to delete, e.g. nic1.2',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages
    resource = instances_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client),
    )
    request = messages.ComputeInstancesDeleteNetworkInterfaceRequest(
        project=resource.project,
        instance=resource.instance,
        zone=resource.zone,
        networkInterfaceName=args.network_interface,
    )
    operation = client.instances.DeleteNetworkInterface(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations'
    )
    operation_poller = poller.Poller(client.instances)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        f'Deleting network interface {args.network_interface} from instance'
        f' {resource.Name()}',
    )
