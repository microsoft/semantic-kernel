# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Delete batches command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a batch job."""
  detailed_help = {
      'EXAMPLES':
          """\
          To delete a batch job, run:

            $ {command} my-batch-job --region=us-central1
          """
    }

  @staticmethod
  def Args(parser):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)

    flags.AddAsync(parser)
    flags.AddBatchResourceArg(parser, 'delete', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    messages = dataproc.messages

    batch_id = args.CONCEPTS.batch.Parse()

    request = messages.DataprocProjectsLocationsBatchesDeleteRequest(
        name=batch_id.RelativeName())

    console_io.PromptContinue(
        message="The batch '{}' will be deleted.".format(batch_id.Name()),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.')

    dataproc.client.projects_locations_batches.Delete(request)

    if args.async_:
      log.status.Print("Deleting batch '{}'.".format(batch_id.Name()))
      return

    def _GetJob(job_ref):
      return dataproc.client.projects_locations_batches.Get(
          dataproc.messages.DataprocProjectsLocationsBatchesGetRequest(
              name=job_ref))

    util.WaitForResourceDeletion(
        _GetJob, batch_id.RelativeName(), message='Waiting for batch deletion')

    log.DeletedResource(batch_id.RelativeName())
