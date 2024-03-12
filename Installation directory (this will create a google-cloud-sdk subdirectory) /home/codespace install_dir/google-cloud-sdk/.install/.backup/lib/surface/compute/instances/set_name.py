# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for renaming virtual machine instances.."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class InstanceSetName(base.SilentCommand):
  """Set name for Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)

    parser.add_argument(
        '--new-name',
        required=True,
        help="""\
        Specifies the new name of the instance. """)

  def _CreateSetNameRequest(self, client, instance_ref, name):
    return (client.apitools_client.instances,
            'SetName',
            client.messages.ComputeInstancesSetNameRequest(
                instancesSetNameRequest=client.messages.InstancesSetNameRequest(
                    name=name, currentName=instance_ref.Name()),
                **instance_ref.AsDict()))

  def _CreateGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances,
            'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    get_request = self._CreateGetRequest(client, instance_ref)
    objects = client.MakeRequests([get_request])

    if args.new_name == objects[0].name:
      return objects[0]

    set_request = self._CreateSetNameRequest(client, instance_ref,
                                             args.new_name)

    return client.MakeRequests([set_request],
                               followup_overrides=[args.new_name])


InstanceSetName.detailed_help = {
    'brief': 'Set the name of a Compute Engine virtual machine.',
    'DESCRIPTION': """
        ``{command}'' lets you change the name of a virtual machine.
        """,
    'EXAMPLES': """
        To change the name of ``instance-1'' to ``instance-2'':

          $ {command} instance-1 --new-name=instance-2
        """,
}
