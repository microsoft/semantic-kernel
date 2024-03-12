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
"""Command for obtaining details about jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.printers import export_printer
from googlecloudsdk.command_lib.run.printers import job_printer
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.resource import resource_printer


class Describe(base.DescribeCommand):
  """Obtain details about jobs."""

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To describe a job:

              $ {command} my-job
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(),
        'Job to describe.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)

    resource_printer.RegisterFormatter(
        job_printer.JOB_PRINTER_FORMAT, job_printer.JobPrinter, hidden=True)
    parser.display_info.AddFormat(job_printer.JOB_PRINTER_FORMAT)
    resource_printer.RegisterFormatter(
        export_printer.EXPORT_PRINTER_FORMAT,
        export_printer.ExportPrinter,
        hidden=True)

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def Run(self, args):
    """Show details about a job execution."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack(), version_override='v1')
    job_ref = args.CONCEPTS.job.Parse()

    with serverless_operations.Connect(conn_context) as client:
      job = client.GetJob(job_ref)

    if not job:
      raise exceptions.ArgumentError('Cannot find job [{}].'.format(
          job_ref.Name()))
    return job
