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
"""Command to move a folder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Move(base.UpdateCommand):
  """Move a folder to a new position within the same organization.

  Move the given folder under a new parent folder or under the organization.
  Exactly one of --folder or --organization must be provided.

  This command can fail for the following reasons:
      * There is no folder with the given ID.
      * There is no parent with the given type and ID.
      * The new parent is not in the same organization of the given folder.
      * Permission missing for performing this move.

  ## EXAMPLES

  The following command moves a folder with the ID `123456789` into a
  folder with the ID `2345`:

    $ {command} 123456789 --folder=2345

  The following command moves a folder with the ID `123456789` into an
  organization with ID `1234`:

    $ {command} 123456789 --organization=1234
  """

  @staticmethod
  def Args(parser):
    flags.FolderIdArg('you want to move.').AddToParser(parser)
    flags.OperationAsyncFlag().AddToParser(parser)
    flags.AddParentFlagsToParser(parser)

  def Run(self, args):
    flags.CheckParentFlags(args)
    messages = folders.FoldersMessages()
    move_request = messages.CloudresourcemanagerFoldersMoveRequest(
        foldersId=args.id,
        moveFolderRequest=messages.MoveFolderRequest(
            destinationParent=flags.GetParentFromFlags(args)))
    operation = folders.FoldersService().Move(move_request)
    if args.async_:
      return operation
    else:
      if operation.done and not operation.name:
        log.status.Print('No changes necessary.')
        return
      finished_op = operations.WaitForOperation(operation)
      result = operations.ExtractOperationResponse(finished_op, messages.Folder)
      log.UpdatedResource(result)
