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

"""types delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import composite_types
from googlecloudsdk.command_lib.deployment_manager import dm_util
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def LogResource(request, is_async):
  log.DeletedResource(request.compositeType,
                      kind='composite_type',
                      is_async=is_async)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class Delete(base.DeleteCommand, dm_base.DmCommand):
  """Delete a composite type."""

  detailed_help = {
      'EXAMPLES': """\
          To delete a composite type, run:

            $ {command} my-composite-type
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddAsyncFlag(parser)
    composite_types.AddCompositeTypeNameFlag(parser)

  def Run(self, args):
    """Run 'types delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    composite_type_ref = composite_types.GetReference(self.resources, args.name)
    if not args.quiet:
      prompt_message = 'Are you sure you want to delete [{0}]?'.format(
          args.name)
      if not console_io.PromptContinue(message=prompt_message, default=False):
        raise exceptions.OperationError('Deletion aborted by user.')

    request = (self.messages.
               DeploymentmanagerCompositeTypesDeleteRequest(
                   project=composite_type_ref.project,
                   compositeType=args.name))

    response = dm_write.Execute(self.client, self.messages, self.resources,
                                request, args.async_,
                                self.client.compositeTypes.Delete, LogResource)
    dm_util.LogOperationStatus(response, 'Delete')
