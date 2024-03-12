# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for perform maintenance on Google Compute Engine instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class PerformMaintenance(base.UpdateCommand):
  """Perform maintenance of Google Compute Engine instance."""

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))

    request_protobuf = messages.ComputeInstancesPerformMaintenanceRequest(
        **instance_ref.AsDict())
    request = (client.apitools_client.instances, 'PerformMaintenance',
               request_protobuf)
    return holder.client.MakeRequests([request])


PerformMaintenance.detailed_help = {
    'brief':
        'Perform maintenance of Google Compute Engine instance',
    'EXAMPLES':
        """\
        To perform customer-triggered maintenance on an instance named ``{0}''
        located in zone ``{1}'', run:

          $ {2} {0} --zone={1}
        """.format('test-instance', 'us-east1-d', '{command}')
}
