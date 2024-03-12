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
"""Command to delete an operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.metastore import operations_util as operations_api_util
from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.metastore import resource_args
from googlecloudsdk.command_lib.metastore import util as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To delete a Dataproc Metastore operation with the name
          `operation-1` in location `us-central1`, run:

          $ {command} operation-1 --location=us-central1

          To delete multiple Dataproc Metastore services with the name
          `operation-1` and `operation-2` in the same location
          `us-central1`, run:

          $ {command} operation-1 operation-2 --location=us-central1
        """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete one or more completed Dataproc Metastore operations."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'to delete', plural=True)

  def Run(self, args):
    op_refs = args.CONCEPTS.operations.Parse()

    console_io.PromptContinue(
        message=command_util.ConstructList(
            'Deleting the following operations:', [
                '[%s] in [%s]' % (op_ref.operationsId, op_ref.locationsId)
                for op_ref in op_refs
            ]),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    encountered_errors = False
    for op_ref in op_refs:
      try:
        operations_api_util.Delete(
            op_ref.RelativeName(), release_track=self.ReleaseTrack())
        failed = None
      except apitools_exceptions.HttpError as e:
        exc = exceptions.HttpException(e)
        failed = exc.payload.status_message
        encountered_errors = True

      log.DeletedResource(
          op_ref.RelativeName(), kind='operation', failed=failed)

    if encountered_errors:
      raise api_util.Error('Some deletions did not succeed.')
