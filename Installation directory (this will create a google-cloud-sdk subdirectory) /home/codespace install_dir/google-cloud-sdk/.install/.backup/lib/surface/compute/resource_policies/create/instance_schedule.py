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
"""Create resource policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util


def _CommonArgs(parser):
  """A helper function."""

  flags.MakeResourcePolicyArg().AddArgument(parser)
  flags.AddCommonArgs(parser)
  parser.add_argument(
      '--timezone',
      help="""
      Timezone used in interpreting schedule. The value of this field must be
      a time zone name from the tz database
      http://en.wikipedia.org/wiki/Tz_database
    """)
  parser.add_argument(
      '--vm-start-schedule',
      help="""
      Schedule for starting the instance, specified using standard CRON format.
    """)
  parser.add_argument(
      '--vm-stop-schedule',
      help="""
      Schedule for stopping the instance, specified using standard CRON format.
    """)

  parser.add_argument(
      '--initiation-date',
      type=arg_parsers.Datetime.Parse,
      help="""
     The start time of the schedule policy. The timestamp must be
     an RFC3339 valid string.""")

  parser.add_argument(
      '--end-date',
      type=arg_parsers.Datetime.Parse,
      help="""The expiration time of the schedule policy. The timestamp must be
        an RFC3339 valid string.""")


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateInstanceSchedulePolicy(base.CreateCommand):
  """Create a Compute Engine instance schedule resource policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = flags.MakeResourcePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    resource_policy = util.MakeInstanceSchedulePolicy(policy_ref, args,
                                                      messages)
    create_request = messages.ComputeResourcePoliciesInsertRequest(
        resourcePolicy=resource_policy,
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Insert', create_request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateInstanceSchedulePolicyBeta(CreateInstanceSchedulePolicy):
  """Create a Compute Engine instance schedule resource policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateInstanceSchedulePolicyAlpha(CreateInstanceSchedulePolicyBeta):
  """Create a Compute Engine instance schedule resource policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)


CreateInstanceSchedulePolicy.detailed_help = {
    'DESCRIPTION':
        """\
Create a Compute Engine instance schedule resource policy.
""",
    'EXAMPLES':
        """\
To create an instance schedule resource policy that has a daily start operation at 8 AM and a daily stop operation at 5 PM for the UTC timezone, run:

  $ {command} my-resource-policy --description="daily policy" --vm-start-schedule="0 8 * * *" --vm-stop-schedule="0 17 * * *" --timezone="UTC" --region=REGION

Use the initiation date and end date to limit when the policy is active. To create an instance schedule resource policy with initiation and end dates, run:

  $ {command} my-resource-policy --description="limited daily policy" --vm-start-schedule="0 8 * * *" --vm-stop-schedule="0 17 * * *" --timezone="UTC" --region=REGION --initiation-date="2021-01-01T00:00:00.000Z" --end-date="2021-02-01T00:00:00.000Z"
"""
}
