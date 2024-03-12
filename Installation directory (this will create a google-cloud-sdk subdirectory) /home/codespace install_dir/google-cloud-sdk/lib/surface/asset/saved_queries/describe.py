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
"""Command to describe a Cloud Asset Inventory saved query."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils


class Describe(base.Command):
  """Describe a Cloud Asset Inventory saved query."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Describe a Cloud Asset Inventory saved query.
      """,
      'EXAMPLES':
          """\
        To describe a saved query with query id 'query1' in project 'p1', run:

          $ {command} query1 --project=p1
      """
  }

  @staticmethod
  def Args(parser):
    flags.AddParentArgs(parser, 'Project of the saved query.',
                        'Organization of the saved query.',
                        'Folder of the saved query.')
    query_id_helper_text = (
        'Asset Saved Query identifier being described. '
        'It must be unique under the'
        ' specified parent resource: project/folder/organization.')

    flags.AddSavedQueriesQueryId(parser, query_id_helper_text)

  def Run(self, args):
    parent = asset_utils.GetSavedQueriesParent(args.organization, args.project,
                                               args.folder)
    client = client_util.AssetSavedQueriesClient(parent)
    return client.Describe(args)
