# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command to create a new folder."""

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
class Create(base.CreateCommand):
  """Create a new folder.

  Creates a new folder in the given parent folder or organization.

  ## EXAMPLES

  The following command creates a folder with the name `abc` into a
  folder with the ID `2345`:

    $ {command} --display-name=abc --folder=2345

  The following command creates a folder with the name `abc` into an
  organization with ID `1234`:

    $ {command} --display-name=abc --organization=1234
  """

  @staticmethod
  def Args(parser):
    flags.AddParentFlagsToParser(parser)
    flags.OperationAsyncFlag().AddToParser(parser)
    base.Argument(
        '--display-name',
        required=True,
        help='Friendly display name to use for the new folder.',
    ).AddToParser(parser)
    flags.TagsFlag().AddToParser(parser)

  def Run(self, args):
    flags.CheckParentFlags(args)
    messages = folders.FoldersMessages()
    tags = flags.GetTagsFromFlags(args, messages.Folder.TagsValue)
    operation = folders.FoldersService().Create(
        messages.CloudresourcemanagerFoldersCreateRequest(
            parent=flags.GetParentFromFlags(args),
            folder=messages.Folder(displayName=args.display_name, tags=tags),
        )
    )
    if args.async_:
      return operation
    else:
      finished_operation = operations.WaitForOperation(operation)
      result = operations.ExtractOperationResponse(finished_operation,
                                                   messages.Folder)
      log.CreatedResource(result)
      return result
