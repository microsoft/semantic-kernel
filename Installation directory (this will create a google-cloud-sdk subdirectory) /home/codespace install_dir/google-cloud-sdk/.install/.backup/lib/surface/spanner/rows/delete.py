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
"""Command for spanner rows delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.command_lib.spanner import write_util
from googlecloudsdk.core import resources


class Delete(base.DeleteCommand):
  # pylint:disable=line-too-long
  """Delete a row in a Cloud Spanner database.

  ## EXAMPLES

  To delete a row with primary keys of SingerId=1,SingName=abc in table Singers
  under my-database and my-instance, run:

      $ {command} --table=Singers --database=my-database --instance=my-instance --keys=1,abc
  """

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddDatabaseResourceArg(parser, 'in which to delete a row',
                                         False)
    parser.add_argument(
        '--table',
        required=True,
        type=str,
        help='The Cloud Spanner table name.')
    parser.add_argument(
        '--keys',
        required=True,
        metavar='KEY',
        type=arg_parsers.ArgList(),
        help='The primary key values of the row to delete.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    database_ref = args.CONCEPTS.database.Parse()
    # DDL(Data Definition Language) is needed to get the schema of the current
    # database and table so that we know the type of each column (e.g. INT64)
    # user wants to delete.
    ddl = databases.GetDdl(database_ref)
    table = write_util.Table.FromDdl(ddl, args.table)

    mutation = database_sessions.MutationFactory.Delete(table, args.keys)

    # To commit a transaction in a session, we need to create one and delete it
    # at the end.
    session_name = database_sessions.Create(database_ref)
    session = resources.REGISTRY.ParseRelativeName(
        relative_name=session_name.name,
        collection='spanner.projects.instances.databases.sessions')
    try:
      return database_sessions.Commit(session, [mutation])
    finally:
      database_sessions.Delete(session)
