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
"""Command for listing Jobs."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


class List(commands.List):
  """List jobs."""

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To list all jobs in all regions:

              $ {command}
         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to list jobs in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([namespace_presentation]).AddToParser(parser)
    parser.display_info.AddFormat(
        'table('
        '{ready_column},'
        'name:label=JOB,'
        'region:label=REGION,'
        'status.latestCreatedExecution.creationTimestamp'
        '.date("%Y-%m-%d %H:%M:%S %Z"):label="LAST RUN AT",'
        'creation_timestamp.date("%Y-%m-%d %H:%M:%S %Z"):label=CREATED,'
        'author:label="CREATED BY"):({alias})'.format(
            ready_column=pretty_print.READY_COLUMN,
            alias=commands.SATISFIES_PZS_ALIAS,
        )
    )
    parser.display_info.AddUriFunc(cls._GetResourceUri)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List jobs."""
    # Use the mixer for global request if there's no --region flag.
    namespace_ref = args.CONCEPTS.namespace.Parse()
    if not args.IsSpecified('region'):
      client = global_methods.GetServerlessClientInstance(api_version='v1')
      self.SetPartialApiEndpoint(client.url)
      # Don't consider region property here, we'll default to all regions
      return commands.SortByName(global_methods.ListJobs(client, namespace_ref))

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    with serverless_operations.Connect(conn_context) as client:
      self.SetCompleteApiEndpoint(conn_context.endpoint)
      return commands.SortByName(client.ListJobs(namespace_ref))
