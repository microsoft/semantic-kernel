# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to list assets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.command_lib.util.args import common_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the Cloud assets."""

  # pylint: disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      List the Cloud assets. Note
      that to list a project different from the project you want to bill, you
      can use  --billing-project or authenticate with a service account.
      See https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/gcloud-asset
      for examples of using a service account.
      """,
      'EXAMPLES':
          """\
      To list a snapshot of assets of type 'compute.googleapis.com/Disk' in
      project 'test-project' at '2019-03-05T00:00:00Z', run:

        $ {command} --project='test-project' --asset-types='compute.googleapis.com/Disk' --snapshot-time='2019-03-05T00:00:00Z'
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
    flags.AddSnapshotTimeArgs(parser)
    flags.AddAssetTypesArgs(parser)
    flags.AddListContentTypeArgs(parser)
    flags.AddRelationshipTypesArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForExport(args.organization, args.project,
                                                args.folder)
    client = client_util.AssetListClient(parent)
    return client.List(args)
