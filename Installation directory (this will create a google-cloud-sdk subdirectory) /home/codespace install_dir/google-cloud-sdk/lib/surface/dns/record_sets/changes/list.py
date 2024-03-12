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

"""gcloud dns record-sets changes list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """View the list of changes that have been made to your record-sets.

  This command displays the list of changes that have been made to your
  record-sets.

  ## EXAMPLES

  To see the list of changes, run:

    $ {command}

  To see the list of first 10 changes, run:

    $ {command} --limit=10
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)
    parser.add_argument(
        '--sort-order', default=None, required=False,
        choices=['ascending', 'descending'],
        help='Sort order for listing.')
    parser.display_info.AddFormat(flags.CHANGES_FORMAT)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    api_version = 'v1'
    # If in the future there are differences between API version, do NOT use
    # this patter of checking ReleaseTrack. Break this into multiple classes.
    if self.ReleaseTrack() == base.ReleaseTrack.BETA:
      api_version = 'v1beta2'
    elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha2'

    dns_client = util.GetApiClient(api_version)

    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='dns.managedZones')

    return list_pager.YieldFromList(
        dns_client.changes,
        dns_client.MESSAGES_MODULE.DnsChangesListRequest(
            project=zone_ref.project,
            managedZone=zone_ref.Name(),
            sortOrder=args.sort_order),
        limit=args.limit, field='changes')
