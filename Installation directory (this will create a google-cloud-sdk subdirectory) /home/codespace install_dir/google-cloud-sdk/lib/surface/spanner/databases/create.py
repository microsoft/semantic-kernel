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
"""Command for spanner databases create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args


class Create(base.CreateCommand):
  """Create a Cloud Spanner database."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To create an empty Cloud Spanner database, run:

          $ {command} testdb --instance=my-instance-id

        To create a Cloud Spanner database with populated schema, run:

          $ {command} testdb --instance=my-instance-id
              --ddl='CREATE TABLE mytable (a INT64, b INT64) PRIMARY KEY(a)'

        To create a Cloud Spanner database with the PostgreSQL dialect, run:

          $ {command} testdb --instance=my-instance-id
              --database-dialect=POSTGRESQL
        """),
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddDatabaseResourceArg(parser, 'to create')
    flags.Ddl(help_text='Semi-colon separated DDL (data definition language) '
              'statements to run inside the '
              'newly created database. If there is an error in any statement, '
              'the database is not created. This option is not supported for '
              'the PostgreSQL dialect. Full DDL specification is at '
              'https://cloud.google.com/spanner/docs/data-definition-language'
             ).AddToParser(parser)
    flags.DdlFile(
        help_text='Path of a file that contains semi-colon separated DDL (data '
        'definition language) statements to run inside the newly created '
        'database. If there is an error in any statement, the database is not '
        'created. This option is not supported for the PostgreSQL dialect. '
        'Full DDL specification is at '
        'https://cloud.google.com/spanner/docs/data-definition-language.'
        ' If --ddl_file is set, --ddl is ignored. One line comments starting '
        'with -- are ignored.').AddToParser(parser)
    flags.ProtoDescriptorsFile(
        help_text='Path of a file that contains a protobuf-serialized '
        'google.protobuf.FileDescriptorSet message. To generate it, install and'
        ' run `protoc` with --include_imports and --descriptor_set_out.'
    ).AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.DatabaseCompleter)
    resource_args.AddKmsKeyResourceArg(parser,
                                       'to create the Cloud Spanner database')
    flags.DatabaseDialect(
        help_text='The SQL dialect of the Cloud Spanner Database. '
        'GOOGLE_STANDARD_SQL is the default.'
    ).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    database_ref = args.CONCEPTS.database.Parse()
    instance_ref = database_ref.Parent()
    kms_key_name_or_names = resource_args.GetAndValidateKmsKeyName(args)
    op = databases.Create(
        instance_ref,
        args.database,
        flags.SplitDdlIntoStatements(args),
        flags.GetProtoDescriptors(args),
        kms_key_name_or_names,
        args.database_dialect,
    )
    if args.async_:
      return op
    return database_operations.Await(op, 'Creating database')
