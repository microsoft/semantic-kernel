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
"""Command for describing queued resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.queued_resources import flags

DETAILED_HELP = {
    'EXAMPLES':
        """\
  To describe a Compute Engine queued resource with the name 'queued-resource-1', run:

    $ {command} queued-resource-1
  """,
}


class Describe(base.DescribeCommand):
  """Describe a Compute Engine queued resource.

  *{command}* describes a Compute Engine queued resource.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    Describe.QueuedResourcesArg = flags.MakeQueuedResourcesArg(plural=False)
    Describe.QueuedResourcesArg.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    queued_resource_ref = Describe.QueuedResourcesArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    requests = [(client.apitools_client.zoneQueuedResources, 'Get',
                 client.messages.ComputeZoneQueuedResourcesGetRequest(
                     project=queued_resource_ref.project,
                     zone=queued_resource_ref.zone,
                     queuedResource=queued_resource_ref.queuedResource))]
    return client.MakeRequests(requests)[0]
