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
"""recommender API insights Mark Accepted command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import insight
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags

DETAILED_HELP = {
    'EXAMPLES':
        """
        To mark an insight as ACCEPTED:

          $ {command} abcd-1234 --project=project-id --location=global --insight-type=google.compute.firewall.Insight --etag=abc123
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class MarkAccepted(base.Command):
  r"""Mark an insight's state as ACCEPTED.

     Mark an insight's state as ACCEPTED. Can be applied to insights in ACTIVE
     or ACCEPTED state. The following are currently supported: project,
     billing_account, folder, and organization.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddParentFlagsToParser(parser)
    parser.add_argument(
        'INSIGHT',
        type=str,
        help='Insight id which will be marked as accepted',
    )
    parser.add_argument(
        '--location', metavar='LOCATION', required=True, help='Location')
    parser.add_argument(
        '--insight-type',
        metavar='INSIGHT_TYPE',
        required=True,
        help='Insight Type of the insights')
    parser.add_argument(
        '--etag', required=True, metavar='etag', help='Etag of a insight')
    parser.add_argument(
        '--state-metadata',
        type=arg_parsers.ArgDict(min_length=1),
        default={},
        help='State metadata for recommendation, in format of --state-metadata=key1=value1,key2=value2',
        metavar='KEY=VALUE',
        action=arg_parsers.StoreOnceAction)

  def Run(self, args):
    """Run 'gcloud recommender insights mark-accepted'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The result insights after being marked as accepted
    """
    client = insight.CreateClient(self.ReleaseTrack())
    name = flags.GetInsightName(args)
    return client.MarkAccepted(name, args.state_metadata, args.etag)
