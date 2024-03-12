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
"""Bare Metal Solution instance update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.mps.mps_client import MpsClient
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.mps import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Marketplace Solution instance.

          This call returns immediately, but the update operation may take
          several minutes to complete. To check if the operation is complete,
          use the `describe` command for the instance.
        """,
    'EXAMPLES':
        """
          To update an instance called ``my-instance'' in region ``us-central1'',
          to 3 memoryGib and 0.5 virtualCpuCores, run:

          $ {command} my-instance update --region=us-central1 --memory_gib=3
          --virtual_cpu_cores=0.5
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Marketplace Solution instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInstanceArgToParser(parser, positional=True)
    flags.AddInstanceMemoryGibArgToParse(parser, required=False)
    flags.AddInstanceVirtualCpuCoresArgToParse(parser, required=False)

  def Run(self, args):
    client = MpsClient()
    instance = args.CONCEPTS.instance.Parse()
    product = properties.VALUES.mps.product.Get(required=True)

    memory_gib = getattr(args, 'memory_gib', None)
    virtual_cpu_cores = getattr(args, 'virtual_cpu_cores', None)
    if memory_gib is None and virtual_cpu_cores is None:
      raise exceptions.Error('At least one of '
                             '`--memory-gib` or'
                             '`--virtual-cpu-cores` '
                             'is required')
    op_ref = client.UpdateInstance(
        product=product,
        instance_resource=instance, memory_gib=memory_gib,
        virtual_cpu_cores=virtual_cpu_cores)

    if op_ref.done:
      log.UpdatedResource(instance.Name(), kind='Instance')
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='marketplacesolutions.projects.locations.operations',
        api_version='v1alpha1')
    poller = waiter.CloudOperationPollerNoResources(client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.UpdatedResource(instance.Name(), kind='instance')
    return res

Update.detailed_help = DETAILED_HELP
