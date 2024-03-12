# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to delete an operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To delete the operation ``operation-1'', run:

            $ {command} operation-1
        """
}


class Delete(base.DeleteCommand):
  """Delete one or more completed Cloud Composer operations.

  Delete operations that are done. If more than one operation is specified,
  all deletes will be attempted. If any of the deletes fail, those operations
  and their failure messages will be listed on the standard error, and the
  command will exit with a non-zero status.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'to delete', plural=True)

  def Run(self, args):
    op_refs = args.CONCEPTS.operations.Parse()

    console_io.PromptContinue(
        message=command_util.ConstructList(
            'Deleting the following operations: ', [
                '[%s] in [%s]' % (op_ref.operationsId, op_ref.locationsId)
                for op_ref in op_refs
            ]),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    encountered_errors = False
    for op_ref in op_refs:
      try:
        operations_api_util.Delete(op_ref, release_track=self.ReleaseTrack())
        failed = None
      except apitools_exceptions.HttpError as e:
        exc = exceptions.HttpException(e)
        failed = exc.payload.status_message
        encountered_errors = True

      log.DeletedResource(
          op_ref.RelativeName(), kind='operation', failed=failed)

    if encountered_errors:
      raise command_util.Error('Some deletions did not succeed.')
