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
"""Command to delete one or more Dataproc Metastore federations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.metastore import federations_util as federations_api_util
from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.metastore import delete_util
from googlecloudsdk.command_lib.metastore import resource_args
from googlecloudsdk.command_lib.metastore import util as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To delete a Dataproc Metastore federation with the name
          `my-metastore-federation` in location `us-central1`, run:

          $ {command} my-metastore-federation --location=us-central1

          To delete multiple Dataproc Metastore federations with the name
          `federation-1` and `federation-2` in the same location
          `us-central1`, run:

          $ {command} federation-1 federation-2 --location=us-central1
        """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete one or more Dataproc Metastore federations.

  If run asynchronously with `--async`, exits after printing
  one or more operation names that can be used to poll the status of the
  deletion(s) via:

    {top_command} metastore operations describe
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddFederationResourceArg(
        parser, 'to delete', plural=True, required=True, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    env_refs = args.CONCEPTS.federations.Parse()
    console_io.PromptContinue(
        message=command_util.ConstructList(
            'Deleting the following federations:', [
                '[{}] in [{}]'.format(env_ref.federationsId,
                                      env_ref.locationsId)
                for env_ref in env_refs
            ]),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    waiter = delete_util.FederationDeletionWaiter(
        release_track=self.ReleaseTrack())
    encountered_errors = False
    for env_ref in env_refs:
      operation = None
      failed = None
      try:
        operation = federations_api_util.Delete(
            env_ref.RelativeName(), release_track=self.ReleaseTrack())
      except apitools_exceptions.HttpError as e:
        exc = exceptions.HttpException(e)
        failed = exc.payload.status_message
        encountered_errors = True
      else:
        waiter.AddPendingDelete(
            federation_name=env_ref.RelativeName(), operation=operation)
      finally:
        log.DeletedResource(
            env_ref.RelativeName(),
            kind='federation',
            is_async=True,
            details=None if encountered_errors else
            'with operation [{0}]'.format(operation.name),
            failed=failed)

    if not args.async_:
      encountered_errors = waiter.Wait() or encountered_errors
    if encountered_errors:
      raise api_util.FederationDeleteError(
          'Some requested deletions did not succeed.')
