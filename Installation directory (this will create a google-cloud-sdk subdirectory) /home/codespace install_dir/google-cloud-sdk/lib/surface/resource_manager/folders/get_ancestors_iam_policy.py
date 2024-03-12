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
"""Command to get IAM policy for a folder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import policies_flags
from googlecloudsdk.command_lib.resource_manager import flags


class GetIamPolicy(base.ListCommand):
  """Get IAM policies for a folder and its ancestors.

  Get IAM policies for a folder and its ancestors, given a folder ID.

  ## EXAMPLES

  To get IAM policies for folder ``3589215982'' and its ancestors, run:

    $ {command} 3589215982
  """

  @staticmethod
  def Args(parser):
    flags.GetFolderResourceArg('get IAM policy for.').AddToParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    policies_flags.AddIncludeDenyFlag(parser)

  def Run(self, args):
    return folders.GetAncestorsIamPolicy(args.folder_id, args.include_deny,
                                         self.ReleaseTrack())
