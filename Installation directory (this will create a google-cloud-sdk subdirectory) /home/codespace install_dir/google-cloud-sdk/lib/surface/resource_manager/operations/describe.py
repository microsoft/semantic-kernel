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
"""Command to show metadata for a specified folder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.command_lib.resource_manager import tag_arguments


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Show metadata for an operation.

  Show metadata for an operation, given a valid operation ID.

  This command can fail for the following reasons:
      * The operation specified does not exist.
      * You do not have permission to view the operation.

  ## EXAMPLES

  The following command prints metadata for an operation with the
  ID `fc.3589215982`:

    $ {command} fc.3589215982
  """

  @staticmethod
  def Args(parser):
    flags.OperationIdArg('you want to describe.').AddToParser(parser)
    tag_arguments.AddLocationArgToParser(parser, (
        'Region or zone of the Operation to get. This field is not required if '
        'the Operation is on a global resource such as a Project or TagKey.'))

  def Run(self, args):
    location = args.location if args.IsSpecified('location') else None
    with endpoint_utils.CrmEndpointOverrides(location):
      return operations.GetOperationV3(args.id)
