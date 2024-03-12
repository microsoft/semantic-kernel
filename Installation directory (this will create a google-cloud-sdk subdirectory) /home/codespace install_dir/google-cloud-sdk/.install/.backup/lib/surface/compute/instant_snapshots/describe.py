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
"""Command for describing instant snapshot."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instant_snapshots import flags as ips_flags


def _CommonArgs(parser):
  Describe.ips_arg = ips_flags.MakeInstantSnapshotArg(plural=False)
  Describe.ips_arg.AddArgument(parser, operation_type='describe')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Compute Engine instant snapshot."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    ips_ref = Describe.ips_arg.ResolveAsResource(args, holder.resources)

    if ips_ref.Collection() == 'compute.instantSnapshots':
      service = client.apitools_client.instantSnapshots
      request_type = messages.ComputeInstantSnapshotsGetRequest
    elif ips_ref.Collection() == 'compute.regionInstantSnapshots':
      service = client.apitools_client.regionInstantSnapshots
      request_type = messages.ComputeRegionInstantSnapshotsGetRequest

    return client.MakeRequests([(service, 'Get',
                                 request_type(**ips_ref.AsDict()))])

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describe a Compute Engine instant snapshot in beta."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Describe a Compute Engine instant snapshot in alpha."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


Describe.detailed_help = {
    'brief': 'Describe a Compute Engine instant snapshot',
    'DESCRIPTION': """\
        *{command}* displays all data associated with a Compute
        Engine instant snapshot in a project.
        """,
    'EXAMPLES': """\
        To describe the instant snapshot 'instant-snapshot-1' in zone 'us-east1-a', run:

            $ {command} instant-snapshot-1 --zone=us-east1-a
        """,
}
