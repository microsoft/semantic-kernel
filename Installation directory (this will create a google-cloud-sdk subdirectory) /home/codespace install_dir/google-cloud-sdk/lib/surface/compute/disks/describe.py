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

"""Command for describing disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags


def _CommonArgs(parser):
  Describe.disk_arg.AddArgument(parser, operation_type='describe')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Compute Engine disk."""

  @staticmethod
  def Args(parser):
    Describe.disk_arg = disks_flags.MakeDiskArg(plural=False)
    _CommonArgs(parser)

  def Collection(self):
    return 'compute.disks'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    disk_ref = Describe.disk_arg.ResolveAsResource(args, holder.resources)

    if disk_ref.Collection() == 'compute.disks':
      service = client.disks
      request_type = messages.ComputeDisksGetRequest
    elif disk_ref.Collection() == 'compute.regionDisks':
      service = client.regionDisks
      request_type = messages.ComputeRegionDisksGetRequest

    return service.Get(request_type(**disk_ref.AsDict()))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describe a Compute Engine disk."""

  @staticmethod
  def Args(parser):
    Describe.disk_arg = disks_flags.MakeDiskArg(plural=False)
    _CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Describe a Compute Engine disk."""

  @staticmethod
  def Args(parser):
    Describe.disk_arg = disks_flags.MakeDiskArg(plural=False)
    _CommonArgs(parser)


Describe.detailed_help = {
    'brief': 'Describe a Compute Engine disk',
    'DESCRIPTION':
        """\
        *{command}* displays all data associated with a Compute Engine
        disk in a project.
        """,
    'EXAMPLES':
        """\
        To describe the disk 'my-disk' in zone 'us-east1-a', run:

            $ {command} my-disk --zone=us-east1-a
        """,
}
