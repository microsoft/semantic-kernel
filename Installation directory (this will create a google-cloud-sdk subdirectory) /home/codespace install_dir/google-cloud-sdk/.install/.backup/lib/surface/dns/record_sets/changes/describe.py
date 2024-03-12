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

"""gcloud dns record-sets changes describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


class Describe(base.DescribeCommand):
  """View the details of a change.

  This command displays the details of the specified change.

  ## EXAMPLES

  To display the details of a change, run:

    $ {command} change_id
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)
    parser.add_argument(
        'change_id', metavar='CHANGE_ID',
        help='The ID of the change you want details for.')

  def Run(self, args):
    api_version = 'v1'
    # If in the future there are differences between API version, do NOT use
    # this patter of checking ReleaseTrack. Break this into multiple classes.
    if self.ReleaseTrack() == base.ReleaseTrack.BETA:
      api_version = 'v1beta2'
    elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha2'

    dns_client = util.GetApiClient(api_version)
    change_ref = util.GetRegistry(api_version).Parse(
        args.change_id,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
            'managedZone': args.MakeGetOrRaise('--zone'),
        },
        collection='dns.changes')

    return dns_client.changes.Get(
        dns_client.MESSAGES_MODULE.DnsChangesGetRequest(
            project=change_ref.project,
            managedZone=change_ref.managedZone,
            changeId=change_ref.changeId))
