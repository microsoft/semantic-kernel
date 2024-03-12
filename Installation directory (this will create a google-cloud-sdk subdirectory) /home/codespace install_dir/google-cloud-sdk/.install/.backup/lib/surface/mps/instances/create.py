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
"""Marketplace Solution instance create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.mps.mps_client import MpsClient
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.mps import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a Marketplace Solution Instance.
        """,
    'EXAMPLES':
        """
          To create an instance called ``my-instance'' in region ``us-central1'', with
          requested boot image of AIX72_ORD_Cloud, 2 Gib of memory, an s922 system type,
          a shared core type, and 0.25 cores, run:

          $ {command} my-instance  --region=us-central1 --boot-image-name=AIX72_ORD_Cloud --memory-gib=2 --network-attachment-name=dev-net --system-type=s922 --virtual-cpu-type=UNCAPPED_SHARED --virtual-cpu-cores=0.25

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Marketplace Solution Instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInstanceArgToParser(parser, positional=True)
    flags.AddInstanceBootImageNameArgToParse(parser=parser)
    flags.AddInstanceMemoryGibArgToParse(parser=parser)
    flags.AddInstanceNetworkAttachmentNameArgToParse(parser=parser)
    flags.AddInstanceSystemTypeArgToParse(parser=parser)
    flags.AddInstanceVirtualCpuCoresArgToParse(parser=parser)
    flags.AddInstanceVirtualCpuTypeArgToParse(parser=parser)

  def Run(self, args):
    # pylint: disable=line-too-long
    instance = args.CONCEPTS.instance.Parse()
    client = MpsClient()
    product = properties.VALUES.mps.product.Get(required=True)

    op_ref = client.CreateInstance(product,
                                   instance_resource=instance,
                                   boot_image_name=args.boot_image_name,
                                   system_type=args.system_type,
                                   memory_gib=args.memory_gib,
                                   network_attachment_names=args.network_attachment_name,
                                   virtual_cpu_cores=args.virtual_cpu_cores,
                                   virtual_cpu_type=args.virtual_cpu_type)

    if op_ref.done:
      log.CreatedResource(instance.Name(), kind='Instance')
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='marketplacesolutions.projects.locations.operations',
        api_version='v1alpha1')
    poller = waiter.CloudOperationPollerNoResources(client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.CreatedResource(instance.Name(), kind='Instance')
    return res


Create.detailed_help = DETAILED_HELP
