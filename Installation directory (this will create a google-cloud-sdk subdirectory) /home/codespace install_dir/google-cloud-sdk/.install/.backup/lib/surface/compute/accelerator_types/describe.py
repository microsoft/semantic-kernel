# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for describing accelerator types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.accelerator_types import flags


class Describe(base.DescribeCommand):
  """Describe a Compute Engine accelerator type."""

  @staticmethod
  def Args(parser):
    flags.ACCELERATOR_TYPES_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = flags.ACCELERATOR_TYPES_ARG.ResolveAsResource(args, holder.resources)

    client = holder.client.apitools_client
    messages = holder.client.messages

    request = messages.ComputeAcceleratorTypesGetRequest(
        project=ref.project, zone=ref.zone, acceleratorType=ref.Name())

    resources = holder.client.MakeRequests(
        [(client.acceleratorTypes, 'Get', request)])
    return resources[0]


Describe.detailed_help = {
    'brief':
        'Describe Compute Engine accelerator types',
    'DESCRIPTION':
        """\
        *{command}* displays all data associated with a Compute Engine
        accelerator type.
        """,
}
