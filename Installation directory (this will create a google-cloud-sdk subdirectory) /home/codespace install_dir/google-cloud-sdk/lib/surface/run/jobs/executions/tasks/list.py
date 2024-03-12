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
"""Command for listing job tasks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


class List(commands.List):
  """List tasks."""

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To list all tasks for an execution:

              $ {command} --execution=my-execution
         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    execution_presentation = presentation_specs.ResourcePresentationSpec(
        '--execution',
        resource_args.GetExecutionResourceSpec(),
        'Execution for which to list tasks.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([execution_presentation]).AddToParser(parser)
    flags.AddTaskFilterFlags(parser)
    parser.display_info.AddFormat(
        'table('
        '{ready_column},'
        'index,'
        'running_state:label=STATE,'
        'name:label=TASK,'
        'start_time.date("%Y-%m-%d %H:%M:%S %Z"):label=STARTED,'
        'completion_time.date("%Y-%m-%d %H:%M:%S %Z"):label=COMPLETED,'
        'retries):({alias})'.format(
            ready_column=pretty_print.READY_COLUMN,
            alias=commands.SATISFIES_PZS_ALIAS,
        )
    )

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List tasks of a job execution."""
    execution_ref = args.CONCEPTS.execution.Parse()

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    with serverless_operations.Connect(conn_context) as client:
      self.SetCompleteApiEndpoint(conn_context.endpoint)
      ret = client.ListTasks(execution_ref.Parent(), execution_ref.Name(),
                             args.filter_flags or None)
      return sorted(ret, key=lambda x: x.index)
