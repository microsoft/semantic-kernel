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

"""Cancel operation command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Cancel(base.Command):
  """Cancel an active operation.

  Cancel an active operation.

  ## EXAMPLES

  To cancel an operation, run:

    $ {command} operation_id
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddOperationResourceArg(parser, 'cancel', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    operation_ref = args.CONCEPTS.operation.Parse()

    request = dataproc.messages.DataprocProjectsRegionsOperationsCancelRequest(
        name=operation_ref.RelativeName())

    console_io.PromptContinue(
        message="The operation '{0}' will be cancelled.".format(
            args.operation),
        cancel_on_no=True,
        cancel_string='Cancellation aborted by user.')

    dataproc.client.projects_regions_operations.Cancel(request)
    # TODO(b/36050484) Check that operation was cancelled.

    log.status.write('Cancelled [{0}].\n'.format(args.operation))
