# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for Managed Microsoft AD operations cancel."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
from googlecloudsdk.api_lib.active_directory import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import display
from googlecloudsdk.command_lib.active_directory import flags
from googlecloudsdk.command_lib.active_directory import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Cancel(base.Command):
  """Cancel a Managed Microsoft AD operation."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddOperationResourceArg(parser, 'to cancel')

  def Run(self, args):
    # resource represents the Managed Microsoft AD operation.
    resource = args.CONCEPTS.name.Parse()
    client = util.GetClientForResource(resource)
    messages = util.GetMessagesForResource(resource)
    get_req = \
        messages.ManagedidentitiesProjectsLocationsGlobalOperationsGetRequest(
            name=resource.RelativeName())
    op = client.projects_locations_global_operations.Get(get_req)
    operation_string = io.StringIO()
    print_format = display.Displayer(self, args).GetFormat()
    resource_printer.Print(op, print_format, out=operation_string)

    if not console_io.PromptContinue(
        message='{}\nThis operation will be canceled'.format(
            operation_string.getvalue())):
      raise exceptions.ActiveDirectoryError('Cancel aborted by user.')
    cancel_req = \
        messages.ManagedidentitiesProjectsLocationsGlobalOperationsCancelRequest(
            name=resource.RelativeName())
    client.projects_locations_global_operations.Cancel(cancel_req)
    log.status.write('Canceled [{0}].\n'.format(resource.RelativeName()))


Cancel.detailed_help = {
    'brief':
        'Cancel a Managed Microsoft AD operation.',
    'EXAMPLES':
        """
        The following command cancels an operation called
        `operation-1484002552235-425b144f8c3f8-81aa4b49-0830d1e9`:

          $ {command} operation-1484002552235-425b144f8c3f8-81aa4b49-0830d1e9
        """
}
