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

from googlecloudsdk.api_lib.recommender import flag_utils as api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags


DETAILED_HELP = {
    'EXAMPLES':
        """
        To describe a Recommender Config:

          $ {command} --project=${PROJECT} --location=${LOCATION} --recommender=${RECOMMENDER}
        """,
}


def AddArgsToParser(parser):
  """Add flags to parser.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command.
  """
  parser.add_argument(
      '--project', metavar='PROJECT', required=True, help='Project number')
  parser.add_argument(
      '--location', metavar='LOCATION', required=True, help='Location')
  parser.add_argument(
      '--recommender',
      metavar='RECOMMENDER',
      required=True,
      help='Recommender for the recommender config')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.Command):
  r"""Describe a Recommender Config.

     Describe a Recommender Config based on given project, location, and
     recommender.
  """
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    AddArgsToParser(parser)

  def Run(self, args):
    """Run 'gcloud recommender recommenderConfigs describe'.

    Args:
      args: argparse.Namespace, The arguments that the command was invoked with.

    Returns:
      The result recommender config to describe.
    """
    api_version = api_utils.GetApiVersion(self.ReleaseTrack())
    is_insight_api = False
    recommender_service = api_utils.GetConfigServiceFromArgs(
        api_version, is_insight_api)
    parent_ref = flags.GetConfigsParentFromFlags(args, is_insight_api)
    request = api_utils.GetDescribeConfigRequestFromArgs(
        parent_ref, is_insight_api, api_version)
    return recommender_service.GetConfig(request)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(base.Command):
  r"""Describe a Recommender Config.

     Describe a Recommender Config based on given project, location, and
     recommender.
  """
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    AddArgsToParser(parser)

  def Run(self, args):
    """Run 'gcloud recommender recommenderConfigs describe'.

    Args:
      args: argparse.Namespace, The arguments that the command was invoked with.

    Returns:
      The result recommender config to describe.
    """
    api_version = api_utils.GetApiVersion(self.ReleaseTrack())
    is_insight_api = False
    recommender_service = api_utils.GetConfigServiceFromArgs(
        api_version, is_insight_api)
    parent_ref = flags.GetConfigsParentFromFlags(args, is_insight_api)
    request = api_utils.GetDescribeConfigRequestFromArgs(
        parent_ref, is_insight_api, api_version)
    return recommender_service.GetConfig(request)
