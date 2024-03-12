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
"""Command to delete an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import delete_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To delete the environment named ``environment-1'', run:

            $ {command} environment-1
        """
}


class Delete(base.DeleteCommand):
  """Delete one or more Cloud Composer environments.

  Environments cannot be deleted unless they are in one of the RUNNING or
  ERROR states. If run asynchronously with `--async`, exits after printing
  one or more operation names that can be used to poll the status of the
  deletion(s) via:

    {top_command} composer operations describe

  If any of the environments are already in the process of being deleted,
  the original deletion operations are waited on (default) or printed
  (`--async`).
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'to delete', plural=True, required=True, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    env_refs = args.CONCEPTS.environments.Parse()
    console_io.PromptContinue(
        message=command_util.ConstructList(
            'Deleting the following environments: ', [
                '[{}] in [{}]'.format(env_ref.environmentsId,
                                      env_ref.locationsId)
                for env_ref in env_refs
            ]),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    waiter = delete_util.EnvironmentDeletionWaiter(
        release_track=self.ReleaseTrack())
    encountered_errors = False
    for env_ref in env_refs:
      operation = None
      failed = None
      details = None
      try:
        operation = environments_api_util.Delete(
            env_ref, release_track=self.ReleaseTrack())
      except apitools_exceptions.HttpError as e:
        failed = exceptions.HttpException(e).payload.status_message
        encountered_errors = True
      else:
        details = 'with operation [{0}]'.format(operation.name)
        waiter.AddPendingDelete(
            environment_name=env_ref.RelativeName(), operation=operation)
      finally:
        log.DeletedResource(
            env_ref.RelativeName(),
            kind='environment',
            is_async=True,
            details=details,
            failed=failed)

    if not args.async_:
      encountered_errors = waiter.Wait() or encountered_errors
    if encountered_errors:
      raise command_util.EnvironmentDeleteError(
          'Some requested deletions did not succeed. '
          'Please, refer to '
          'https://cloud.google.com/composer/docs/how-to/managing/updating '
          'and Composer Delete Troubleshooting pages to resolve this issue.')
