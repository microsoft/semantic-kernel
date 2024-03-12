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
"""Command for describing disk types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disk_types import flags
from googlecloudsdk.command_lib.compute.flags import GetDefaultScopeLister
from googlecloudsdk.command_lib.compute.scope import ScopeEnum


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Compute Engine disk type."""

  @staticmethod
  def Args(parser):
    Describe.DiskTypeArg = flags.MakeDiskTypeArg(regional=False)
    Describe.DiskTypeArg.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    disk_type = Describe.DiskTypeArg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=ScopeEnum.ZONE,
        scope_lister=GetDefaultScopeLister(client))

    if disk_type.Collection() == 'compute.diskTypes':
      service = client.apitools_client.diskTypes
      message_type = client.messages.ComputeDiskTypesGetRequest
    elif disk_type.Collection() == 'compute.regionDiskTypes':
      service = client.apitools_client.regionDiskTypes
      message_type = client.messages.ComputeRegionDiskTypesGetRequest

    return client.MakeRequests([(service, 'Get', message_type(
        **disk_type.AsDict()))])[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):

  @staticmethod
  def Args(parser):
    Describe.DiskTypeArg = flags.MakeDiskTypeArg(regional=True)
    Describe.DiskTypeArg.AddArgument(parser, operation_type='describe')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):

  @staticmethod
  def Args(parser):
    Describe.DiskTypeArg = flags.MakeDiskTypeArg(regional=True)
    Describe.DiskTypeArg.AddArgument(parser, operation_type='describe')

Describe.detailed_help = {
    'brief': 'Describe a Compute Engine disk type',
    'DESCRIPTION': """\
        *{command}* displays all data associated with a Compute Engine
        disk type.
        """,
}
