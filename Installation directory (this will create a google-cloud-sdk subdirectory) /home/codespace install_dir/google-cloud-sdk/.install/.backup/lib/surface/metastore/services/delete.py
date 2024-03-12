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
"""Command to delete one or more Dataproc Metastore services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.metastore import services_util as services_api_util
from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.metastore import delete_util
from googlecloudsdk.command_lib.metastore import resource_args
from googlecloudsdk.command_lib.metastore import util as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To delete a Dataproc Metastore service with the name
          `my-metastore-service` in location `us-central1`, run:

          $ {command} my-metastore-service --location=us-central1

          To delete multiple Dataproc Metastore services with the name
          `service-1` and `service-2` in the same location
          `us-central1`, run:

          $ {command} service-1 service-2 --location=us-central1
        """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete one or more Dataproc Metastore services.

  If run asynchronously with `--async`, exits after printing
  one or more operation names that can be used to poll the status of the
  deletion(s) via:

    {top_command} metastore operations describe
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddServiceResourceArg(
        parser, 'to delete', plural=True, required=True, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    env_refs = args.CONCEPTS.services.Parse()
    console_io.PromptContinue(
        message=command_util.ConstructList('Deleting the following services:', [
            '[{}] in [{}]'.format(env_ref.servicesId, env_ref.locationsId)
            for env_ref in env_refs
        ]),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    waiter = delete_util.ServiceDeletionWaiter(
        release_track=self.ReleaseTrack())
    encountered_errors = False
    for env_ref in env_refs:
      operation = None
      failed = None
      try:
        operation = services_api_util.Delete(
            env_ref.RelativeName(), release_track=self.ReleaseTrack())
      except apitools_exceptions.HttpError as e:
        encountered_errors = True
      else:
        details = 'with operation [{0}]'.format(operation.name)
        waiter.AddPendingDelete(
            service_name=env_ref.RelativeName(), operation=operation)
      finally:
        log.DeletedResource(
            env_ref.RelativeName(),
            kind='service',
            is_async=True,
            details=None if encountered_errors else
            'with operation [{0}]'.format(operation.name),
            failed=failed)

    if not args.async_:
      encountered_errors = waiter.Wait() or encountered_errors
    if encountered_errors:
      raise api_util.ServiceDeleteError(
          'Some requested deletions did not succeed.')
