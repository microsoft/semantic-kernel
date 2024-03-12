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
"""Command to analyze resource move for a specified asset and destination."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base


def AddProjectArgs(parser):
  parser.add_argument(
      '--project',
      metavar='PROJECT_ID',
      required=True,
      help='The project ID or number to perform the analysis.')


def AddDestinationGroup(parser):
  destination_group = parser.add_group(mutex=True, required=True)
  AddDestinationOrgArgs(destination_group)
  AddDestinationFolderArgs(destination_group)


def AddDestinationOrgArgs(parser):
  parser.add_argument(
      '--destination-organization',
      metavar='ORGANIZATION_ID',
      required=False,
      help='The destination organization ID to perform the analysis.')


def AddDestinationFolderArgs(parser):
  parser.add_argument(
      '--destination-folder',
      metavar='FOLDER_ID',
      required=False,
      help='The destination folder ID to perform the analysis.')


def AddBlockersOnlyArgs(parser):
  parser.add_argument(
      '--blockers-only',
      metavar='BLOCKERS_ONLY',
      required=False,
      default=False,
      help='Determines whether to perform analysis against blockers only. '
      'Leaving it empty means the full analysis will be performed including '
      'warnings and blockers for the specified resource move.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AnalyzeMove(base.Command):
  """Analyzes resource move."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Analyze resource migration from its current resource hierarchy.""",
      'EXAMPLES':
          """\
      To analyze the impacts of moving a project to a different organization, run:

          $ gcloud asset analyze-move --project=YOUR_PROJECT_ID --destination-organization=ORGANIZATION_ID

      To analyze the impacts of moving a project to a different folder, run:

          $ gcloud asset analyze-move --project=YOUR_PROJECT_ID --destination-folder=FOLDER_ID

      To analyze only the blockers of moving a project to a different folder, run:

          $ gcloud asset analyze-move --project=YOUR_PROJECT_ID --destination-folder=FOLDER_ID --blockers-only=true
      """
  }

  @staticmethod
  def Args(parser):
    AddProjectArgs(parser)
    AddDestinationGroup(parser)
    AddBlockersOnlyArgs(parser)

  def Run(self, args):
    client = client_util.AnalyzeMoveClient()
    return client.AnalyzeMove(args)
