# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to list operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.vmware import flags as vmware_flags

_EXAMPLES = """
To list all operations in location ``us-west1'', run:

$ {command} --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class List(base.ListCommand):
  """List operations."""
  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    vmware_flags.AddLocationResourceArg(parser, 'to list operations')
    parser.display_info.AddFormat(constants.OPERATIONS_FORMAT)

  def Run(self, args):
    """Runs the describe command."""
    operation_client = operations.OperationsClient()
    # Regex pattern matches VMware user cluster and VMware admin cluster.
    vmware_operation_predicate = (
        'metadata.target ~ projects/.+/locations/.+/vmware')

    if args.filter:
      args.filter = vmware_operation_predicate + ' AND ' + args.filter
    else:
      args.filter = vmware_operation_predicate

    return operation_client.List(args)
