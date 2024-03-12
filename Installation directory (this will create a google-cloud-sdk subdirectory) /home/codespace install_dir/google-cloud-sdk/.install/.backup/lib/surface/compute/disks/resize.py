# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for setting size of instance group manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core.console import console_io

CONTINUE_WITH_RESIZE_PROMPT = textwrap.dedent("""
    This command increases disk size. This change is not reversible.
    For more information, see:
    https://cloud.google.com/sdk/gcloud/reference/compute/disks/resize""")


def _CommonArgs(parser):
  Resize.DISKS_ARG.AddArgument(parser)
  parser.add_argument(
      '--size',
      required=True,
      type=arg_parsers.BinarySize(lower_bound='1GB'),
      help="""\
        Indicates the new size of the disks. The value must be a whole
        number followed by a size unit of ``GB'' for gigabyte, or
        ``TB'' for terabyte. If no size unit is specified, GB is
        assumed. For example, ``10GB'' will produce 10 gigabyte disks.
        Disk size must be a multiple of 1 GB.
        """)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Resize(base.Command):
  """Set size of a persistent disk."""

  @classmethod
  def Args(cls, parser):
    Resize.DISKS_ARG = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(parser)

  def Run(self, args):
    """Issues request for resizing a disk."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    size_gb = utils.BytesToGb(args.size)
    disk_refs = Resize.DISKS_ARG.ResolveAsResource(
        args, holder.resources)

    console_io.PromptContinue(
        message=CONTINUE_WITH_RESIZE_PROMPT,
        cancel_on_no=True)

    requests = []

    for disk_ref in disk_refs:
      if disk_ref.Collection() == 'compute.disks':
        request = client.messages.ComputeDisksResizeRequest(
            disk=disk_ref.Name(),
            project=disk_ref.project,
            zone=disk_ref.zone,
            disksResizeRequest=client.messages.DisksResizeRequest(
                sizeGb=size_gb))
        requests.append((client.apitools_client.disks, 'Resize', request))
      elif disk_ref.Collection() == 'compute.regionDisks':
        request = client.messages.ComputeRegionDisksResizeRequest(
            disk=disk_ref.Name(),
            project=disk_ref.project,
            region=disk_ref.region,
            regionDisksResizeRequest=client.messages.RegionDisksResizeRequest(
                sizeGb=size_gb))
        requests.append((client.apitools_client.regionDisks, 'Resize', request))

    return client.MakeRequests(requests)

Resize.detailed_help = {
    'brief': 'Resize a disk or disks',
    'DESCRIPTION': """\
        *{command}* resizes a Compute Engine disk(s).

        Only increasing disk size is supported. Disks can be resized
        regardless of whether they are attached.

    """,
    'EXAMPLES': """\
        To resize a disk called example-disk-1 to new size 6TB, run:

           $ {command} example-disk-1 --size=6TB

        To resize two disks called example-disk-2 and example-disk-3 to
        new size 6TB, run:

           $ {command} example-disk-2 example-disk-3 --size=6TB

        This assumes that original size of each of these disks is 6TB or less.
        """}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ResizeBeta(Resize):

  @classmethod
  def Args(cls, parser):
    Resize.DISKS_ARG = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ResizeAlpha(Resize):

  @classmethod
  def Args(cls, parser):
    Resize.DISKS_ARG = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(parser)


ResizeAlpha.detailed_help = Resize.detailed_help
