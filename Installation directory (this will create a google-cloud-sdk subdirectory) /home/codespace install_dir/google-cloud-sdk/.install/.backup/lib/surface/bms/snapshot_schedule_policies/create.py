# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Bare Metal Solution snapshot schedule policies create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a Bare Metal Solution snapshot schedule policy.
        """,
    'EXAMPLES':
        """
          To create a policy called ``my-policy'' in project ``my-project''
          with description ``my-description'' a schedule that runs every 3
          hours and labels 'key1=value1' and 'key2=value2', run:

          $ {command} my-policy --project=my-project --description=my-description --schedule="crontab_spec=0 */3 * * *,retention_count=10,prefix=example" --labels=key1=value1,key2=value2
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Bare Metal Solution snapshot schedule policy."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSnapshotSchedulePolicyArgToParser(
        parser, positional=True)
    flags.AddSnapshotScheduleArgListToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    parser.add_argument('--description',
                        help='Description of the policy.')

  def Run(self, args):
    policy = args.CONCEPTS.snapshot_schedule_policy.Parse()
    description = args.description
    client = BmsClient()
    return client.CreateSnapshotSchedulePolicy(
        policy_resource=policy,
        labels=labels_util.ParseCreateArgs(
            args, client.messages.SnapshotSchedulePolicy.LabelsValue),
        description=description,
        schedules=args.schedule)


Create.detailed_help = DETAILED_HELP
