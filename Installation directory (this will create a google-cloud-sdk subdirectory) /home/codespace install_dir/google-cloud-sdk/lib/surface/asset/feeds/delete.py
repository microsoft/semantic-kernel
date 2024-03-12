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
"""Command to delete a Cloud Asset Inventory Feed.."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils


class Delete(base.Command):
  """Delete a Cloud Asset Inventory Feed."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Delete a Cloud Asset Inventory Feed.
      """,
      'EXAMPLES':
          """\
        To delete a feed 'feed1' in project 'p1', run:

          $ {command} feed1 --project=p1
      """
  }
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    flags.AddParentArgs(parser, 'project of the feed.',
                        'Organization of the feed.', 'Folder of the feed.')
    flags.AddFeedIdArgs(parser, 'Asset feed identifier to delete.')

  def Run(self, args):
    parent = asset_utils.GetFeedParent(args.organization, args.project,
                                       args.folder)
    client = client_util.AssetFeedClient(parent)
    client.Delete(args)
