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

"""Batches cancel command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Cancel(base.Command):
  """Cancel a batch job without removing batch resources."""
  detailed_help = {
      'EXAMPLES':
          """\
          To cancel a batch job "my-batch-job" in the "us-central1" region, run:

            $ {command} my-batch-job --region=us-central1
          """
  }

  @staticmethod
  def Args(parser):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    flags.AddBatchResourceArg(parser, 'cancel', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    batch_id = args.CONCEPTS.batch.Parse()

    console_io.PromptContinue(
        message='The batch [{0}] will be cancelled.'.format(
            batch_id.Name()),
        cancel_on_no=True,
        cancel_string='Cancellation aborted by user.')

    # Get the batch workload to obtain operation reference.
    batch = dataproc.client.projects_locations_batches.Get(
        dataproc.messages.DataprocProjectsLocationsBatchesGetRequest(
            name=batch_id.RelativeName()))

    log.status.Print('Canceling batch [{}].'.format(batch_id.Name()))

    dataproc.client.projects_regions_operations.Cancel(
        dataproc.messages.DataprocProjectsRegionsOperationsCancelRequest(
            name=batch.operation))
