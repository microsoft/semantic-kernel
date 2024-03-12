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
"""recommender API recommendations Describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import recommendation
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.Command):
  r"""Describe a recommendation for a Cloud project.

     Describe a recommendation. This currently supports the following parent
     entities: project, billing account, folder, and organization.

     ## EXAMPLES
     To describe a recommendation:

      $ {command} RECOMMENDATION_ID --project=${PROJECT} --location=${LOCATION}
      --recommender=${RECOMMENDER}
  """

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
        help='Recommendation to describe',
    )
    parser.add_argument(
        '--location', metavar='LOCATION', required=True, help='Location')
    parser.add_argument(
        '--recommender',
        metavar='RECOMMENDER',
        required=True,
        help='Recommender of the recommendations')

  def Run(self, args):
    """Run 'gcloud recommender recommendations describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The result recommendations to describe
    """
    client = recommendation.CreateClient(self.ReleaseTrack())
    name = flags.GetRecommendationName(args)
    return client.Get(name)
