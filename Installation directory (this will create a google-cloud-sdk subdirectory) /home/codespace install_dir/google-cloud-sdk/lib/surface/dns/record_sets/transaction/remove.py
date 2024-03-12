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

"""gcloud dns record-sets transaction remove command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dns import resource_record_sets as rrsets_util
from googlecloudsdk.api_lib.dns import transaction_util as trans_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Remove(base.Command):
  r"""Append a record-set deletion to the transaction.

  This command appends a record-set deletion to the transaction.

  ## EXAMPLES

  To remove an A record, run:

    $ {command} --zone=MANAGED_ZONE --name=my.domain. --ttl=1234 \
        --type=A "1.2.3.4"

  To remove a TXT record with multiple data values, run:

    $ {command} --zone=MANAGED_ZONE --name=my.domain. --ttl=2345 \
        --type=TXT "Hello world" "Bye world"
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
        help='DNS name of the record-set to be removed.')
    parser.add_argument(
        '--ttl', required=True, type=int,
        help='TTL for the record-set to be removed.')
    parser.add_argument(
        '--type', required=True,
        help='Type of the record-set to be removed.')
    parser.add_argument(
        'rrdatas', nargs='+',
        help='DNS name of the record-set to be removed.')

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

    dns = util.GetApiClient(api_version)

    # Ensure the record to be removed exists
    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='dns.managedZones')

    record_to_remove = rrsets_util.CreateRecordSetFromArgs(
        args,
        zone_ref.project,
        api_version=api_version,
        allow_extended_records=self._IsBetaOrAlpha())

    existing_records = [record for record in list_pager.YieldFromList(
        dns.resourceRecordSets,
        dns.MESSAGES_MODULE.DnsResourceRecordSetsListRequest(
            project=zone_ref.project,
            managedZone=zone_ref.Name(),
            name=util.AppendTrailingDot(args.name),
            type=args.type),
        field='rrsets')]
    if not existing_records or existing_records[0] != record_to_remove:
      raise trans_util.RecordDoesNotExist('Record to be removed does not exist')

    change.deletions.append(record_to_remove)

    with trans_util.TransactionFile(args.transaction_file, 'w') as trans_file:
      trans_util.WriteToYamlFile(trans_file, change)

    log.status.Print(
        'Record removal appended to transaction at [{0}].'.format(
            args.transaction_file))
