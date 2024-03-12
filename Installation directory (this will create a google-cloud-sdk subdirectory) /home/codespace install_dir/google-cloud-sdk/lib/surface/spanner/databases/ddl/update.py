# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner databases ddl update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Update the DDL for a Cloud Spanner database."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To add a column to a table in the given Cloud Spanner database, run:

          $ {command} my-database-id --instance=my-instance-id
              --ddl='ALTER TABLE test_table ADD COLUMN a INT64'
        """),
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddDatabaseResourceArg(parser, 'of which the ddl to update')
    flags.Ddl(help_text='Semi-colon separated DDL '
              '(data definition language) statements to '
              'run inside the database. If a statement fails, all subsequent '
              'statements in the batch are automatically cancelled.'
             ).AddToParser(parser)
    flags.DdlFile(
        help_text='Path of a file containing semi-colon separated DDL (data '
        'definition language) statements to run inside the database. If a '
        'statement fails, all subsequent statements in the batch are '
        'automatically cancelled. If --ddl_file is set, --ddl is ignored. '
        'One line comments starting with -- are ignored.').AddToParser(parser)
    flags.ProtoDescriptorsFile(
        help_text='Path of a file that contains a protobuf-serialized '
        'google.protobuf.FileDescriptorSet message. To generate it, install and'
        ' run `protoc` with --include_imports and --descriptor_set_out.'
    ).AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    op = databases.UpdateDdl(args.CONCEPTS.database.Parse(),
                             flags.SplitDdlIntoStatements(args),
                             flags.GetProtoDescriptors(args))
    if args.async_:
      return log.status.Print(
          'Schema update in progress. Operation name={}'.format(op.name))
    return database_operations.Await(op, 'Schema updating')
