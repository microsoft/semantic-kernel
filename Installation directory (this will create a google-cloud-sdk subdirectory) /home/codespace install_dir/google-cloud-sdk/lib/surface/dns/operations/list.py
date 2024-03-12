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
"""gcloud dns operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
from googlecloudsdk.api_lib.dns import operations
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags


def _CommonArgs(parser):
  """Add arguments to the parser for `operations list` command."""
  # The operations describe command needs both the zone name and the ID.
  # We need the zone name in the list output otherwise it gets confusing
  # when listing multiple zones. Since the zone name doesn't change, it
  # doesn't matter if we get it from oldValue or newValue.
  parser.display_info.AddFormat("""
      table(
        zoneContext.oldValue.name:label=ZONE_NAME:sort=1,
        id,
        startTime,
        user,
        type
      )
  """)
  base.URI_FLAG.RemoveFromParser(parser)
  base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
  flags.GetZoneResourceArg(
      'Name of one or more zones to read.',
      positional=False, plural=True).AddToParser(parser)


def _List(operations_client, args):
  zone_refs = args.CONCEPTS.zones.Parse()
  return itertools.chain.from_iterable(
      operations_client.List(z, limit=args.limit) for z in zone_refs)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """List Cloud DNS operations.

  This command displays Cloud DNS operations for one or more Cloud DNS
  managed-zones (see `$ gcloud dns managed-zones --help`).

  ## EXAMPLES

  To see the list of all operations for two managed-zones, run:

    $ {command} --zones=zone1,zone2

  To see the last 5 operations for two managed-zones, run:

    $ {command} --zones=zone1,zone2 --sort-by=~start_time --limit=5
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    operations_client = operations.Client.FromApiVersion(api_version)
    return _List(operations_client, args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Cloud DNS operations.

  This command displays Cloud DNS operations for one or more Cloud DNS
  managed-zones (see `$ gcloud dns managed-zones --help`).

  ## EXAMPLES

  To see the list of all operations for two managed-zones, run:

    $ {command} --zones=zone1,zone2

  To see the last 5 operations for two managed-zones, run:

    $ {command} --zones=zone1,zone2 --sort-by=~start_time --limit=5
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    operations_client = operations.Client.FromApiVersion('v1')
    return _List(operations_client, args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Cloud DNS operations.

  This command displays Cloud DNS operations for one or more Cloud DNS
  managed-zones (see `$ gcloud dns managed-zones --help`).

  ## EXAMPLES

  To see the list of all operations for two managed-zones, run:

    $ {command} --zones=zone1,zone2

  To see the last 5 operations for two managed-zones, run:

    $ {command} --zones=zone1,zone2 --sort-by=~start_time --limit=5
  """
