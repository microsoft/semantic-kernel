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
"""recommender API recommendations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import recommendation
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags

DETAILED_HELP = {
    'EXAMPLES':
        """
        To mark a recommendation as SUCCEEDED:

          $ {command} abcd-1234 --project=project-id --location=global --recommender=google.compute.instance.MachineTypeRecommender --etag=abc123 --state-metadata=key1=value1,key2=value2
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class MarkSucceeded(base.Command):
  r"""Mark a recommendation's state as SUCCEEDED.

      Mark a recommendation's state as SUCCEEDED. Can be applied to
      recommendations
      in ACTIVE, CLAIMED, SUCCEEDED, or FAILED state.
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
        'RECOMMENDATION',
        type=str,
        help='Recommendation id which will be marked as succeeded')
    parser.add_argument(
        '--location', metavar='LOCATION', required=True, help='Location')
    parser.add_argument(
        '--recommender',
        metavar='RECOMMENDER',
        required=True,
        help='Recommender of recommendation')
    parser.add_argument(
        '--etag',
        metavar='ETAG',
        required=True,
        help='Etag of a recommendation')
    parser.add_argument(
        '--state-metadata',
        type=arg_parsers.ArgDict(min_length=1),
        default={},
        help='State metadata for recommendation, in format of --state-metadata=key1=value1,key2=value2',
        metavar='KEY=VALUE',
        action=arg_parsers.StoreOnceAction)

  def Run(self, args):
    """Run 'gcloud recommender recommendations mark-succeeded'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The recommendations after being marked as succeeded.
    """
    client = recommendation.CreateClient(self.ReleaseTrack())
    name = flags.GetRecommendationName(args)
    return client.MarkSucceeded(name, args.state_metadata, args.etag)
