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

"""gcloud dns record-sets transaction add command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import resource_record_sets as rrsets_util
from googlecloudsdk.api_lib.dns import transaction_util as trans_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log


class Add(base.Command):
  r"""Append a record-set addition to the transaction.

  This command appends a record-set addition to the transaction.

  For a guide detailing how to manage records, see:
  https://cloud.google.com/dns/records/

  ## EXAMPLES

  To add an A record with an IP address of "1.2.3.4", domain name of
  "my.domain.", and a managed zone "MANAGED_ZONE", run:

    $ {command} "1.2.3.4" \
        --name=my.domain. --ttl=1234 \
        --type=A --zone=MANAGED_ZONE

  To add a TXT record with multiple data values while specifying time to
  live as 14400 seconds, run:

    $ {command} "Hello world" "Bye world" \
        --name=my.domain. --ttl=14400 \
        --type=TXT --zone=MANAGED_ZONE
  """

  @classmethod
  def _IsBetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)
    parser.add_argument(
        '--name', required=True,
        help='DNS or domain name of the record-set to add.')
    parser.add_argument(
        '--ttl', required=True, type=int,
        help='TTL (time to live) for the record-set to add.')
    parser.add_argument(
        '--type', required=True,
        help='DNS record type of the record-set to add.')
    parser.add_argument(
        'rrdatas', nargs='+',
        help='DNS data (Address/CNAME/MX info, etc.) of the record-set to add. '
             'This is RDATA; the format of this information varies depending '
             'on the type and class of the resource record.')

  def Run(self, args):
    api_version = 'v1'
    # If in the future there are differences between API version, do NOT use
    # this patter of checking ReleaseTrack. Break this into multiple classes.
    if self.ReleaseTrack() == base.ReleaseTrack.BETA:
      api_version = 'v1beta2'
    elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha2'

    with trans_util.TransactionFile(args.transaction_file) as trans_file:
      change = trans_util.ChangeFromYamlFile(
          trans_file, api_version=api_version)

    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params=util.GetParamsForRegistry(api_version, args),
        collection='dns.managedZones')
    change.additions.append(
        rrsets_util.CreateRecordSetFromArgs(
            args,
            zone_ref.project,
            api_version=api_version,
            allow_extended_records=self._IsBetaOrAlpha()))

    with trans_util.TransactionFile(args.transaction_file, 'w') as trans_file:
      trans_util.WriteToYamlFile(trans_file, change)

    log.status.Print(
        'Record addition appended to transaction at [{0}].'.format(
            args.transaction_file))
