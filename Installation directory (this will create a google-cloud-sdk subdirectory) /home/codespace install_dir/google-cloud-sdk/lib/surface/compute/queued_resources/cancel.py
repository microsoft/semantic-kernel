# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for deleting queued resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.queued_resources import flags

DETAILED_HELP = {
    'EXAMPLES':
        """\
    To cancel Compute Engine queued resources with the names 'queued-resource-1'
    and 'queued-resource-2', run:

      $ {command} queued-resource-1 queued-resource-2
    """,
}


class Cancel(base.Command):
  """Cancel Compute Engine queued resources.

  *{command}* cancels one or more Compute Engine queued resources.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    Cancel.QueuedResourcesArg = flags.MakeQueuedResourcesArg(plural=True)
    Cancel.QueuedResourcesArg.AddArgument(parser, operation_type='cancel')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    queued_resources_refs = Cancel.QueuedResourcesArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    requests = []
    for queued_resource_ref in queued_resources_refs:
      requests.append((
          client.apitools_client.zoneQueuedResources,
          'Cancel',
          client.messages.ComputeZoneQueuedResourcesCancelRequest(
              project=queued_resource_ref.project,
              zone=queued_resource_ref.zone,
              queuedResource=queued_resource_ref.queuedResource,
              requestId=uuid.uuid4().hex,
          ),
      ))
    return client.MakeRequests(requests)
