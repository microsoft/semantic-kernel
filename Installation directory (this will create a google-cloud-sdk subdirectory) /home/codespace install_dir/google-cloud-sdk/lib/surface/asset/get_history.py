# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to get history of assets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.util.args import common_args


class GetHistory(base.Command):
  """Get the update history of assets that overlaps a time window."""

  detailed_help = {
      'EXAMPLES':
          """\
      To get the history of asset metadata for
      '//compute.googleapis.com/projects/test-project/zones/us-central1-f/instances/instance1'
      between '2018-10-02T15:01:23.045Z' and '2018-12-05T13:01:21.045Z', run:

        $ {command} --project='test-project' --asset-names='//compute.googleapis.com/projects/test-project/zones/us-central1-f/instances/instance1' --start-time='2018-10-02T15:01:23.045Z' --end-time='2018-12-05T13:01:21.045Z' --content-type='resource'

      To get the history of asset iam policy for
      '//cloudresourcemanager.googleapis.com/projects/10179387634'
      between '2018-10-02T15:01:23.045Z' and '2018-12-05T13:01:21.045Z', and
      project '10179387634' is in organization '1060499660910', run:

        $ {command} --organization='1060499660910' --asset-names='//cloudresourcemanager.googleapis.com/projects/10179387634' --start-time='2018-10-02T15:01:23.045Z' --end-time='2018-12-05T13:01:21.045Z' --content-type='iam-policy'
      """
  }

  @staticmethod
  def Args(parser):
    parent_group = parser.add_mutually_exclusive_group(required=True)
    flags.AddOrganizationArgs(
        parent_group, 'The ID of the organization which is the root asset.')
    common_args.ProjectArgument(
        help_text_to_prepend='The project which is the root asset.'
    ).AddToParser(parent_group)
    flags.AddAssetNamesArgs(parser)
    flags.AddContentTypeArgs(parser, required=True)
    flags.AddRelationshipTypesArgs(parser)
    flags.AddStartTimeArgs(parser)
    flags.AddEndTimeArgs(parser)

  def Run(self, args):
    client = client_util.GetHistoryClient()
    return client.GetHistory(args)
