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
"""Recommender API insight type config Describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import base as reco_base
from googlecloudsdk.api_lib.recommender import insight_type_config
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """\
        To describe an insight type configuration, run:

          $ {command} ${INSIGHT_TYPE} --project=${PROJECT} --location=${LOCATION}
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an insight type configuration.

      Describe an insight type configuration based on a given entity (project,
      organization, billing account), location, and insight type.
  """
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddInsightTypeFlagsToParser(parser, [
        reco_base.EntityType.PROJECT, reco_base.EntityType.ORGANIZATION,
        reco_base.EntityType.BILLING_ACCOUNT
    ])

  def Run(self, args):
    """Runs 'gcloud recommender insight-type-config describe'.

    Args:
      args: argparse.Namespace, The arguments that the command was invoked with.

    Returns:
      The result insight type config to describe.
    """
    client = insight_type_config.CreateClient(self.ReleaseTrack())
    config = flags.GetInsightTypeConfigName(args)
    return client.Get(config)
