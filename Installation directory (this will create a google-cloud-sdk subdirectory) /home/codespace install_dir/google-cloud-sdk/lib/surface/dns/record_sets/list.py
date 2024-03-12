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

"""gcloud dns record-sets list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """View the list of record-sets in a managed-zone.

  This command displays the list of record-sets contained within the specified
  managed-zone.

  ## EXAMPLES

  To see the list of all record-sets in my_zone, run:

    $ {command} --zone=my_zone

  To see the list of first 10 record-sets in my_zone, run:

    $ {command} --zone=my_zone --limit=10

  To see the list of 'my.zone.com.' record-sets in my_zone, run:

    $ {command} --zone=my_zone --name="my.zone.com."

  To see the list of 'my.zone.com.' CNAME record-sets in my_zone, run:

    $ {command} --zone=my_zone --name="my.zone.com." --type="CNAME"
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    flags.GetZoneArg().AddToParser(parser)
    flags.GetLocationArg().AddToParser(parser)
    name_type_group = parser.add_group()
    name_type_group.add_argument(
        '--name', required=True,
        help='Only list record-sets with this exact domain name.')
    name_type_group.add_argument(
        '--type', required=False,
        help='Only list records of this type. If present, the --name parameter '
        'must also be present.')
    parser.display_info.AddTransforms(flags.RESOURCERECORDSETS_TRANSFORMS)
    parser.display_info.AddFormat(flags.RESOURCERECORDSETS_FORMAT)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)

    dns_client = util.GetApiClient(api_version)

    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params=util.GetParamsForRegistry(api_version, args),
        collection='dns.managedZones')

    list_request = dns_client.MESSAGES_MODULE.DnsResourceRecordSetsListRequest(
        project=zone_ref.project,
        managedZone=zone_ref.Name(),
        name=util.AppendTrailingDot(args.name),
        type=args.type)

    if api_version == 'v2':
      list_request.location = args.location

    return list_pager.YieldFromList(
        dns_client.resourceRecordSets,
        list_request,
        limit=args.limit,
        field='rrsets')
