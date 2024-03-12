# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Recommender API recommender config Update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import base as reco_base
from googlecloudsdk.api_lib.recommender import recommender_config
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To update a recommender configuration, run:

          $ {command} ${RECOMMENDER} --project=${PROJECT} --location=${LOCATION}
          --etag=\\"123\\" --config-file=config.yaml
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.Command):
  r"""Update a recommender configuration.

      Update a recommender configuration based on a given entity (project,
      organization, billing account),
      location, and recommender.
  """
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddRecommenderFlagsToParser(parser, [
        reco_base.EntityType.PROJECT, reco_base.EntityType.ORGANIZATION,
        reco_base.EntityType.BILLING_ACCOUNT
    ])
    flags.AddConfigFileToParser(parser, 'recommender configuration')
    flags.AddDisplayNameToParser(parser, 'recommender configuration')
    flags.AddValidateOnlyToParser(parser)
    flags.AddEtagToParser(parser, 'recommender configuration')
    flags.AddAnnotationsToParser(parser, 'recommender configuration')

  def Run(self, args):
    """Run 'gcloud recommender recommender-config update'.

    Args:
      args: argparse.Namespace, The arguments that the command was invoked with.

    Returns:
      The result recommender configuration to describe.
    """
    client = recommender_config.CreateClient(self.ReleaseTrack())
    config_name = flags.GetRecommenderConfigName(args)
    return client.Update(config_name, args)
