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
"""Command to update an existing Cloud Asset Inventory Feed."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.command_lib.util.args import repeated


class Update(base.Command):
  """Update an existing Cloud Asset Inventory Feed."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Update an existing Cloud Asset Inventory Feed.
      """,
      'EXAMPLES':
          """\
        To add an asset-type to an existing feed, run:

          $ {command} feed1 --project=p1
          --add-asset-types=pubsub.googleapis.com/Topic
      """
  }

  @staticmethod
  def Args(parser):
    flags.AddParentArgs(parser, 'project of the feed.',
                        'Organization of the feed.', 'Folder of the feed.')
    flags.AddFeedIdArgs(
        parser,
        ('Identifier of the asset feed to update, which must be unique in its '
         'parent resource. Parent resource can be a project, '
         'folder, or an organization. '))
    repeated.AddPrimitiveArgs(
        parser,
        'Feed',
        'asset-names',
        'assetNames',
        additional_help=(
            'See '
            'https://cloud.google.com/apis/design/resource_names#full_resource_name'
            ' for more information.'),
        include_set=False)
    repeated.AddPrimitiveArgs(
        parser,
        'Feed',
        'asset-types',
        'assetTypes',
        additional_help=('See https://cloud.google.com/resource-manager/docs/'
                         'cloud-asset-inventory/overview for all supported '
                         'asset types.'),
        include_set=False)
    repeated.AddPrimitiveArgs(
        parser,
        'Feed',
        'relationship-types',
        'relationshipTypes',
        additional_help=('See https://cloud.google.com/resource-manager/docs/'
                         'cloud-asset-inventory/overview for all supported '
                         'relationship types.'),
        include_set=False)
    flags.AddUpdateFeedContentTypeArgs(parser)
    flags.AddFeedPubSubTopicArgs(parser, False)
    flags.AddUpdateFeedConditionExpressionArgs(parser)
    flags.AddUpdateFeedConditionTitleArgs(parser)
    flags.AddUpdateFeedConditionDescriptionArgs(parser)

  def Run(self, args):
    parent = asset_utils.GetFeedParent(args.organization, args.project,
                                       args.folder)
    client = client_util.AssetFeedClient(parent)
    return client.Update(args)
