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
"""Command for deleting jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import execution
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import deletion
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.Command):
  """Delete a job."""

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To delete a job:

              $ {command} job-name
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(),
        'Job to delete.',
        required=True,
        prefixes=False)
    flags.AddAsyncFlag(parser, default_async_for_cluster=True, is_job=True)
    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)

  def Run(self, args):
    """Delete a job."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    job_ref = args.CONCEPTS.job.Parse()
    with serverless_operations.Connect(conn_context) as client:
      message = 'Job [{}] will be deleted.'.format(job_ref.jobsId)
      if console_io.CanPrompt() and self.HasRunningExecutions(job_ref, client):
        message += (
            ' This job is currently executing; all running executions will be'
            ' stopped and deleted.'
        )
      console_io.PromptContinue(
          message=message,
          throw_if_unattended=True,
          cancel_on_no=True,
      )
      deletion.Delete(job_ref, client.GetJob, client.DeleteJob, args.async_)
    if args.async_:
      pretty_print.Success('Job [{}] is being deleted.'.format(job_ref.jobsId))
    else:
      log.DeletedResource(job_ref.jobsId, 'job')

  def HasRunningExecutions(self, job_ref, client):
    # gcloud-disable-gdu-domain
    label_selector = (
        '{label} = {name}, run.googleapis.com/servingState = Active'.format(
            label=execution.JOB_LABEL, name=job_ref.jobsId
        )
    )
    for _ in client.ListExecutions(
        job_ref.Parent(), label_selector, limit=1, page_size=1
    ):
      return True
    return False
