# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to commit conversion workspaces for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import conversion_workspaces
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import flags as cw_flags

DETAILED_HELP = {
    'DESCRIPTION': """
        Describe database entities in a Database Migration conversion workspace.
        """,
    'EXAMPLES': """\
        To describe the database entities of the source tree in a conversion
        workspace in a project and location `us-central1`, run:

            $ {command} my-conversion-workspace --region=us-central1
        --tree-type=SOURCE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeEntities(base.Command):
  """Describe database entities in a Database Migration conversion workspace."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddConversionWorkspaceResourceArg(parser, 'describe entities')
    cw_flags.AddTreeTypeFlag(parser, required=True)
    cw_flags.AddCommitIdFlag(parser)
    cw_flags.AddUncomittedFlag(parser)
    cw_flags.AddFilterFlag(parser)

    parser.display_info.AddFormat(
        """
          table(
            parentEntity:label=PARENT,
            shortName:label=NAME,
            tree:label=TREE_TYPE,
            entityType:label=ENTITY_TYPE
          )
        """
    )

  def Run(self, args):
    """Describe database entities for a DMS conversion workspace.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A list of entities for the specified conversion workspace and arguments.
    """
    conversion_workspace_ref = args.CONCEPTS.conversion_workspace.Parse()

    cw_client = conversion_workspaces.ConversionWorkspacesClient(
        self.ReleaseTrack()
    )
    return cw_client.DescribeEntities(
        conversion_workspace_ref.RelativeName(), args
    )
