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
"""Command QueryAsset API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import asset_query_printer
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.command_lib.util.args import common_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Query(base.Command):
  """Query the Cloud assets."""

  # pylint: disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Issue an analytical query on Cloud assets using a BigQuery Standard SQL
      compatible statement.
      """,
      'EXAMPLES':
          """\
      To count the number of compute instances, run:

        $ {command} --project='test-project' --statement='SELECT * FROM compute_googleapis_com_Instance'

      To see the query result of the previous job, pass the job-reference from the previous response:

        $ {command} --project='test-project' --job-reference=<job-reference-from>
      """
  }
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    parent_group = parser.add_mutually_exclusive_group(required=True)
    flags.AddOrganizationArgs(
        parent_group, 'The ID of the organization which is the root asset.')
    common_args.ProjectArgument(
        help_text_to_prepend='The project which is the root asset.'
    ).AddToParser(parent_group)
    flags.AddFolderArgs(parent_group,
                        'The ID of the folder which is the root asset.')
    flags.AddQueryArgs(parser)
    flags.AddPageSize(parser)
    flags.AddPageToken(parser)
    flags.AddTimeout(parser)
    flags.AddTimeArgs(parser)
    flags.AddQuerySystemBigQueryArgs(parser)

    parser.display_info.AddFormat(
        asset_query_printer.ASSET_QUERY_PRINTER_FORMAT)

    asset_query_printer.AssetQueryPrinter.Register(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForExport(args.organization, args.project,
                                                args.folder)
    client = client_util.AssetQueryClient(parent)
    resp = client.Query(args)

    return resp
