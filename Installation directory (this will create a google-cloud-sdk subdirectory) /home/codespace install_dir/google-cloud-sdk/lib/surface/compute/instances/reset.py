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

"""Command for resetting an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags

DETAILED_HELP = {
    'brief': 'Reset a virtual machine instance.',
    'DESCRIPTION':
        """\
          *{command}* is used to perform a hard reset on a
        Compute Engine virtual machine.

        This will not perform a clean shutdown of the guest OS on the instance.
        """,
    'EXAMPLES':
        """\
        To reset an instance named ``test-instance'', run:

          $ {command} test-instance
        """
}


class Reset(base.SilentCommand):
  """Reset a virtual machine instance."""

  @staticmethod
  def Args(parser):
    flags.INSTANCES_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_refs = flags.INSTANCES_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))
    request_list = []
    for instance_ref in instance_refs:
      request = client.messages.ComputeInstancesResetRequest(
          instance=instance_ref.Name(),
          project=instance_ref.project,
          zone=instance_ref.zone)

      request_list.append((client.apitools_client.instances, 'Reset', request))
    return client.MakeRequests(request_list)


Reset.detailed_help = DETAILED_HELP
