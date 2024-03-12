# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to update a folder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update the display name of a folder.

  Updates the given folder with new folder name.

  This command can fail for the following reasons:
      * There is no folder with the given ID.
      * The active account does not have permission to update the given
        folder.
      * The new display name is taken by another folder under this folder's
        parent.

  ## EXAMPLES

  The following command updates a folder with the ID `123456789` to have
  the name "Foo Bar and Grill":

    $ {command} 123456789 --display-name="Foo Bar and Grill"
  """

  @staticmethod
  def Args(parser):
    flags.FolderIdArg('you want to update.').AddToParser(parser)
    parser.add_argument(
        '--display-name',
        required=True,
        help='New display name for the folder (unique under the same parent).')

  def Run(self, args):
    folder = folders.GetFolder(args.id)
    folder.displayName = args.display_name
    request = folders.FoldersMessages().CloudresourcemanagerFoldersPatchRequest(
        folder=folder, foldersId=args.id, updateMask='display_name')
    log.UpdatedResource(folders.FoldersService().Patch(request))
