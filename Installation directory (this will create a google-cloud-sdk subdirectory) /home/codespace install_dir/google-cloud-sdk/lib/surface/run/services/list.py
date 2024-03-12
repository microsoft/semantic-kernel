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
"""Command for listing available services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(commands.List):
  """List available services."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To list available services:

              $ {command}
          """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    # Flags specific to connecting to a cluster
    cluster_group = flags.GetClusterArgGroup(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to list services in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([namespace_presentation
                                  ]).AddToParser(cluster_group)

    parser.display_info.AddUriFunc(cls._GetResourceUri)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def _SetFormat(self,
                 args,
                 show_region=False,
                 show_namespace=False,
                 show_description=False):
    """Set display format for output.

    Args:
      args: Namespace, the args namespace
      show_region: bool, True to show region of listed services
      show_namespace: bool, True to show namespace of listed services
      show_description: bool, True to show description of listed services
    """
    columns = [
        pretty_print.READY_COLUMN,
        'firstof(id,metadata.name):label=SERVICE',
    ]
    if show_region:
      columns.append('region:label=REGION')
    if show_namespace:
      columns.append('namespace:label=NAMESPACE')
    if show_description:
      columns.append('description:label=DESCRIPTION')
    columns.extend([
        'domain:label=URL',
        'last_modifier:label="LAST DEPLOYED BY"',
        'last_transition_time:label="LAST DEPLOYED AT"',
    ])
    args.GetDisplayInfo().AddFormat(
        'table({columns}):({alias})'.format(
            columns=','.join(columns), alias=commands.SATISFIES_PZS_ALIAS
        )
    )

  def _GlobalList(self, client):
    """Provides the method to provide a regionless list."""
    return global_methods.ListServices(client)

  def Run(self, args):
    """List available services."""
    is_managed = platforms.GetPlatform() == platforms.PLATFORM_MANAGED
    if is_managed and not args.IsSpecified('region'):
      self._SetFormat(args, show_region=True)
      client = global_methods.GetServerlessClientInstance()
      self.SetPartialApiEndpoint(client.url)
      args.CONCEPTS.namespace.Parse()  # Error if no proj.
      # Don't consider region property here, we'll default to all regions
      return commands.SortByName(self._GlobalList(client))
    else:
      conn_context = connection_context.GetConnectionContext(
          args, flags.Product.RUN, self.ReleaseTrack())
      self._SetFormat(
          args, show_region=is_managed, show_namespace=(not is_managed))
      namespace_ref = args.CONCEPTS.namespace.Parse()
      with serverless_operations.Connect(conn_context) as client:
        self.SetCompleteApiEndpoint(conn_context.endpoint)
        if not is_managed:
          location_msg = ''
          project_msg = ''
          if hasattr(conn_context, 'cluster_location'):
            location_msg = ' in [{}]'.format(conn_context.cluster_location)
          if hasattr(conn_context, 'cluster_project'):
            project_msg = ' in project [{}]'.format(
                conn_context.cluster_project)
          log.status.Print('For cluster [{cluster}]{zone}{project}:'.format(
              cluster=conn_context.cluster_name,
              zone=location_msg,
              project=project_msg))
        return commands.SortByName(client.ListServices(namespace_ref))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaList(List):
  """List available services."""

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)


AlphaList.__doc__ = List.__doc__
