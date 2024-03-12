# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Surface for listing all domain mappings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(commands.List):
  """Lists domain mappings for Cloud Run for Anthos."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          For domain mapping support with fully managed Cloud Run, use
          `gcloud beta run domain-mappings list`.""",
      'EXAMPLES':
          """\
          To list all Cloud Run domain mappings, run:

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
        'Namespace to list domain mappings in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser(
        [namespace_presentation]).AddToParser(cluster_group)

    parser.display_info.AddFormat(
        """table(
        {ready_column},
        metadata.name:label=DOMAIN,
        route_name:label=SERVICE,
        region:label=REGION):({alias})""".format(
            ready_column=pretty_print.READY_COLUMN,
            alias=commands.SATISFIES_PZS_ALIAS,
        )
    )
    parser.display_info.AddUriFunc(cls._GetResourceUri)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List available domain mappings."""
    # domains.cloudrun.com api group only supports v1alpha1 on clusters.
    conn_context = connection_context.GetConnectionContext(
        args,
        flags.Product.RUN,
        self.ReleaseTrack(),
        version_override=('v1alpha1' if
                          platforms.GetPlatform() != platforms.PLATFORM_MANAGED
                          else None))
    namespace_ref = args.CONCEPTS.namespace.Parse()
    with serverless_operations.Connect(conn_context) as client:
      self.SetCompleteApiEndpoint(conn_context.endpoint)
      return commands.SortByName(client.ListDomainMappings(namespace_ref))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaList(List):
  """Lists domain mappings."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list all Cloud Run domain mappings, run:

              $ {command}
          """,
  }

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaList(BetaList):
  """Lists domain mappings."""

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
