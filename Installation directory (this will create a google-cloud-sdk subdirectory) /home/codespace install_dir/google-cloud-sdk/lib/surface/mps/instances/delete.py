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
"""Marketplace Solution instance delete command."""

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
          Delete a Marketplace Solution instance.
        """,
    'EXAMPLES':
        """
          To delete an instance called ``my-instance'' in region
          ``us-central1'', run:

          $ {command} my-instance  --region=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a Marketplace Solution instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInstanceArgToParser(parser, positional=True)

  def Run(self, args):
    instance = args.CONCEPTS.instance.Parse()
    client = MpsClient()
    product = properties.VALUES.mps.product.Get(required=True)

    op_ref = client.DeleteInstance(product, instance)
    if op_ref.done:
      log.DeletedResource(instance.Name(), kind='Instance')
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='marketplacesolutions.projects.locations.operations',
        api_version='v1alpha1')
    poller = waiter.CloudOperationPollerNoResources(client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.DeletedResource(instance.Name(), kind='Instance')
    return res


Delete.detailed_help = DETAILED_HELP
