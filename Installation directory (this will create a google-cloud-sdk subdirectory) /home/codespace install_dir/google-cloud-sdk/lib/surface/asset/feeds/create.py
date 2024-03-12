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
"""Command to create a Cloud Asset Inventory Feed."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils


class Create(base.Command):
  """Create a Cloud Asset Inventory Feed."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Create a new Cloud Asset Inventory Feed for updates on assets.
      """,
      'EXAMPLES':
          """\
          To create a new feed 'feed1' in project 'p1' which alerts on compute
          disks and network resources types, run:

            $ {command} feed1 --project=p1
            --asset-types=compute.googleapis.com/Network,compute.googleapis.com/Disk
            --content-type=resource --pubsub-topic=projects/project1/topics/feed-topic
      """
  }

  @staticmethod
  def Args(parser):
    flags.AddParentArgs(parser, 'project of the feed.',
                        'Organization of the feed.', 'Folder of the feed.')
    flags.AddFeedIdArgs(
        parser,
        ('Asset feed identifier being created, it must be unique under the'
         ' specified parent resource project/folder/organization.'))
    flags.AddFeedCriteriaArgs(parser)
    flags.AddFeedContentTypeArgs(parser)
    flags.AddFeedPubSubTopicArgs(parser, True)
    flags.AddFeedConditionExpressionArgs(parser)
    flags.AddFeedConditionTitleArgs(parser)
    flags.AddFeedConditionDescriptionArgs(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForExport(args.organization, args.project,
                                                args.folder)
    client = client_util.AssetFeedClient(parent)
    return client.Create(args)
