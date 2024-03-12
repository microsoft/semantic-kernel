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
"""Command to delete a trigger."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import triggers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To delete the trigger ``my-trigger'', run:

          $ {command} my-trigger
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an Eventarc trigger."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddTriggerResourceArg(parser, 'The trigger to delete.', required=True)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the delete command."""
    client = triggers.CreateTriggersClient(self.ReleaseTrack())
    trigger_ref = args.CONCEPTS.trigger.Parse()
    operation = client.Delete(trigger_ref)
    if args.async_:
      return operation
    return client.WaitFor(operation, 'Deleting', trigger_ref)


@base.Deprecate(
    is_removed=False,
    warning=(
        'This command is deprecated. '
        'Please use `gcloud eventarc triggers delete` instead.'
    ),
    error=(
        'This command has been removed. '
        'Please use `gcloud eventarc triggers delete` instead.'
    ),
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete an Eventarc trigger."""
