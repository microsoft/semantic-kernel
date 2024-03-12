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

"""gcloud dns record-sets transaction start command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dns import import_util
from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


class Start(base.Command):
  """Start a transaction.

  This command starts a transaction.

  ## EXAMPLES

  To start a transaction, run:

    $ {command} --zone=MANAGED_ZONE
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)

  def Run(self, args):
    api_version = 'v1'
    # If in the future there are differences between API version, do NOT use
    # this patter of checking ReleaseTrack. Break this into multiple classes.
    if self.ReleaseTrack() == base.ReleaseTrack.BETA:
      api_version = 'v1beta2'
    elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha2'

    if os.path.isfile(args.transaction_file):
      raise transaction_util.TransactionFileAlreadyExists(
          'Transaction already exists at [{0}]'.format(args.transaction_file))

    dns = util.GetApiClient(api_version)

    # Get the managed-zone.
    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='dns.managedZones')

    try:
      zone = dns.managedZones.Get(
          dns.MESSAGES_MODULE.DnsManagedZonesGetRequest(
              project=zone_ref.project,
              managedZone=zone_ref.managedZone))
    except apitools_exceptions.HttpError as error:
      raise calliope_exceptions.HttpException(error)

    # Initialize an empty change
    change = dns.MESSAGES_MODULE.Change()

    # Get the SOA record, there will be one and only one.
    # Add addition and deletion for SOA incrementing to change.
    records = [record for record in list_pager.YieldFromList(
        dns.resourceRecordSets,
        dns.MESSAGES_MODULE.DnsResourceRecordSetsListRequest(
            project=zone_ref.project,
            managedZone=zone_ref.Name(),
            name=zone.dnsName,
            type='SOA'),
        field='rrsets')]
    change.deletions.append(records[0])
    change.additions.append(
        import_util.NextSOARecordSet(records[0], api_version=api_version))

    # Write change to transaction file
    try:
      with files.FileWriter(args.transaction_file) as transaction_file:
        transaction_util.WriteToYamlFile(transaction_file, change)
    except Exception as exp:
      msg = 'Unable to write transaction [{0}] because [{1}]'
      msg = msg.format(args.transaction_file, exp)
      raise transaction_util.UnableToAccessTransactionFile(msg)

    log.status.Print('Transaction started [{0}].'.format(
        args.transaction_file))
