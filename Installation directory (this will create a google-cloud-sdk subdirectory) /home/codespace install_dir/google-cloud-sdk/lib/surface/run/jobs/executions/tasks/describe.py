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
"""Command for obtaining details about tasks."""

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
  """Obtain details about tasks."""

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To describe a task:

              $ {command} my-task
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    task_presentation = presentation_specs.ResourcePresentationSpec(
        'TASK',
        resource_args.GetTaskResourceSpec(),
        'Task to describe.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([task_presentation]).AddToParser(parser)

    resource_printer.RegisterFormatter(
        job_printer.TASK_PRINTER_FORMAT,
        job_printer.TaskPrinter,
        hidden=True)
    parser.display_info.AddFormat(job_printer.TASK_PRINTER_FORMAT)

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def Run(self, args):
    """Show details about a job task."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack(), version_override='v1')
    task_ref = args.CONCEPTS.task.Parse()

    with serverless_operations.Connect(conn_context) as client:
      task = client.GetTask(task_ref)

    if not task:
      raise exceptions.ArgumentError('Cannot find task [{}].'.format(
          task_ref.Name()))
    return task
