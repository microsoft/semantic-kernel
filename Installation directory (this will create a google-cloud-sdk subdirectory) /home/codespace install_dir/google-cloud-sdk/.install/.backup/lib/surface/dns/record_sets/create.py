# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""gcloud dns record-sets create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.dns import resource_record_sets as rrsets_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Creates a record-set in a managed-zone."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
          This command creates a record-set contained within the specified
          managed-zone.
          """),
      'EXAMPLES':
          textwrap.dedent("""\
          To create a record-set with dnsName foo.bar.com., record type A,
          rrdata [1.2.3.4, 9.8.7.6] and ttl 60 in my_zone run this:

          $ {command} foo.bar.com. --rrdatas=1.2.3.4,9.8.7.6 --type=A --ttl=60
            --zone=my_zone

          To create a geo routed record-set with dnsName foo.bar.com., record
          type A, routing_policy_data "us-centra1=1.2.3.4,2.3.4.5;us-west1=3.4.5.6,9.8.7.6"
          and ttl 60 in my_zone.

          $ {command} foo.bar.com. --routing_policy_data="us-centra1=1.2.3.4,2.3.4.5;us-west1=3.4.5.6,9.8.7.6"
           --routing_policy_type=GEO --type=A --ttl=60 --zone=my_zone --location=us-east1-a

          To create a record-set with dnsName foo.bar.com., record type A,
          rrdata [1.2.3.4, 9.8.7.6] and ttl 60 in my_zone in us-east1-a run this:

          $ {command} us-east1-a.bar.com. --rrdatas=1.2.3.4,9.8.7.6 --type=A --ttl=60
            --zone=my_zone --location=us-east1-a

          To create a failover type health checked routed record-set with dnsName
          foo.bar.com., record type A, primary routing data "config1", backup
          routing data "us-centra1=1.2.3.4,2.3.4.5;us-west1=3.4.5.6,9.8.7.6", with a
          trickle traffic ratio of 10% to the backup data,
          and ttl 60 in my_zone.

          $ {command} foo.bar.com.  --type=A --ttl=60 \
            --zone=routing-policy-test --routing_policy_type=FAILOVER \
            --routing-policy-primary-data='config1' \
            --routing-policy-backup-data-type=GEO \
            --routing-policy-backup-data='us-centra1=1.2.3.4,2.3.4.5;us-west1=3.4.5.6,9.8.7.6' \
            --backup-data-trickle-ratio=0.1 --enable-health-checking --zone=my_zone

          To create a geo fenced health checked routed record-set with dnsName
          foo.bar.com., record type A, routing-policy-data
          "us-centra1=config1,config2;us-west1=3.4.5.6,9.8.7.6",
          and ttl 60 in my_zone.

          $ {command} foo.bar.com.  --type=A --ttl=60 \
            --zone=routing-policy-test --routing_policy_type=GEO \
            --routing_policy_data='us-centra1=config1,config2;us-west1=3.4.5.6,9.8.7.6' \
            --enable-health-checking --enable-geo-fencing --zone=my_zone
          """)
  }

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    flags.GetZoneArg().AddToParser(parser)
    flags.GetResourceRecordSetsNameArg().AddToParser(parser)
    flags.GetResourceRecordSetsTypeArg(True).AddToParser(parser)
    flags.GetResourceRecordSetsTtlArg(False).AddToParser(parser)
    flags.GetResourceRecordSetsRrdatasArgGroup(
        use_deprecated_names=cls._BetaOrAlpha()).AddToParser(parser)
    flags.GetLocationArg().AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)
    parser.display_info.AddTransforms(flags.RESOURCERECORDSETS_TRANSFORMS)
    parser.display_info.AddFormat(flags.RESOURCERECORDSETS_FORMAT)

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)

    messages = apis.GetMessagesModule('dns', api_version)

    dns_client = util.GetApiClient(api_version)

    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params=util.GetParamsForRegistry(api_version, args),
        collection='dns.managedZones')
    request = messages.DnsResourceRecordSetsCreateRequest(
        project=zone_ref.project,
        managedZone=zone_ref.Name(),
        resourceRecordSet=rrsets_util.CreateRecordSetFromArgs(
            args,
            zone_ref.project,
            api_version,
            allow_extended_records=self._BetaOrAlpha()))

    if api_version == 'v2':
      request.location = args.location

    result = dns_client.resourceRecordSets.Create(request)

    return result
