# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command for listing available reivions."""

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
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(commands.List):
  """List available revisions."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list all revisions for the provided service:

              $ {command} --service=foo
         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    # Flags specific to connecting to a cluster
    cluster_group = flags.GetClusterArgGroup(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to list revisions in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser(
        [namespace_presentation]).AddToParser(cluster_group)

    # Flags not specific to any platform
    flags.AddServiceFlag(parser)

    parser.display_info.AddFormat(
        'table('
        '{ready_column},'
        'name:label=REVISION,'
        'active.yesno(yes="yes", no=""),'
        'service_name:label=SERVICE:sort=1,'
        'creation_timestamp.date("%Y-%m-%d %H:%M:%S %Z"):'
        'label=DEPLOYED:sort=2:reverse,'
        'author:label="DEPLOYED BY"):({alias})'.format(
            ready_column=pretty_print.READY_COLUMN,
            alias=commands.SATISFIES_PZS_ALIAS,
        )
    )
    parser.display_info.AddUriFunc(cls._GetResourceUri)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List available revisions."""
    service_name = args.service
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    namespace_ref = args.CONCEPTS.namespace.Parse()
    with serverless_operations.Connect(conn_context) as client:
      self.SetCompleteApiEndpoint(conn_context.endpoint)
      if platforms.GetPlatform() != platforms.PLATFORM_MANAGED:
        location_msg = ' in [{}]'.format(conn_context.cluster_location)
        log.status.Print('For cluster [{cluster}]{zone}:'.format(
            cluster=conn_context.cluster_name,
            zone=location_msg if conn_context.cluster_location else ''))
      for rev in client.ListRevisions(namespace_ref, service_name,
                                      args.limit, args.page_size):
        yield rev


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaList(List):
  """List available revisions."""

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

AlphaList.__doc__ = List.__doc__
