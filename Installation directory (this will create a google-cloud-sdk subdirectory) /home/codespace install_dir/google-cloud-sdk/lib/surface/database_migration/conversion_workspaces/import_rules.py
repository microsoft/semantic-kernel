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
"""Command to import rules in a conversion workspaces for a database migration from config files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import conversion_workspaces
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import flags as cw_flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ImportRules(base.Command):
  """Import mapping rules in a Database Migration Service conversion workspace."""

  detailed_help = {
      'DESCRIPTION': """
        Import mapping rules in a Database Migration Service conversion
        workspace from a configuration file. For example, for Oracle to
        PostgreSQL migrations that could be an Ora2Pg config file.
        """,
      'EXAMPLES': """\
        To import rules in a conversion workspace:

            $ {command} my-conversion-workspace --region=us-central1
            --file-format=ORA2PG --config-files=PATH1/config1.conf,PATH2/config2.conf
        """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddConversionWorkspaceResourceArg(parser, 'to import rules')
    cw_flags.AddImportFileFormatFlag(parser)
    cw_flags.AddConfigFilesFlag(parser)
    cw_flags.AddAutoCommitFlag(parser)

  def Run(self, args):
    """Import rules in a Database Migration Service conversion workspace.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.
    """
    conversion_workspace_ref = args.CONCEPTS.conversion_workspace.Parse()
    cw_client = conversion_workspaces.ConversionWorkspacesClient(
        self.ReleaseTrack()
    )
    # Import mapping rules is a passthrough method and returns only done: true
    # along with the error (if any)
    result_operation = cw_client.ImportRules(
        conversion_workspace_ref.RelativeName(), args
    )

    if result_operation.error is not None:
      log.status.Print(
          'Imported mapping rules for conversion workspace {} failed with error'
          ' [{}]'.format(
              conversion_workspace_ref.conversionWorkspacesId,
              result_operation.error.message,
          )
      )
    else:
      log.status.Print(
          'Imported mapping rules for conversion workspace {}'.format(
              conversion_workspace_ref.conversionWorkspacesId
          )
      )
