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
"""Command for spanner databases query."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.command_lib.spanner import sql
from googlecloudsdk.command_lib.spanner.sql import QueryHasDml
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'EXAMPLES':
        """\
      To execute a SQL SELECT statement against example-database under
      example-instance, run:

        $ {command} example-database --instance=example-instance --sql='SELECT * FROM MyTable WHERE MyKey = 1'
    """,
}


def CreateSession(args, database_role=None):
  """Creates a session.

  Args:
    args: an argparse namespace. All the arguments that were provided to the
      command invocation.
    database_role: Cloud Spanner database role which owns this session.

  Returns:
    A session reference to be used to execute the sql.
  """
  session_name = database_sessions.Create(args.CONCEPTS.database.Parse(),
                                          database_role)
  return resources.REGISTRY.ParseRelativeName(
      relative_name=session_name.name,
      collection='spanner.projects.instances.databases.sessions')


def AddBaseArgs(parser):
  """Parses provided arguments to add base arguments used for both Beta and GA.

  Args:
    parser: an argparse argument parser.
  """
  resource_args.AddDatabaseResourceArg(parser,
                                       'to execute the SQL query against')
  parser.add_argument(
      '--sql',
      required=True,
      help='The SQL query to issue to the database. Cloud Spanner SQL is '
      'described at https://cloud.google.com/spanner/docs/query-syntax')

  query_mode_choices = {
      'NORMAL': 'Returns only the query result, without any information about '
                'the query plan.',
      'PLAN': 'Returns only the query plan, without any result rows or '
              'execution statistics information.',
      'PROFILE':
          'Returns both the query plan and the execution statistics along '
          'with the result rows.'
  }

  parser.add_argument(
      '--query-mode',
      default='NORMAL',
      type=lambda x: x.upper(),
      choices=query_mode_choices,
      help='Mode in which the query must be processed.')

  parser.add_argument(
      '--enable-partitioned-dml',
      action='store_true',
      help='Execute DML statement using Partitioned DML')

  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      default='10m',
      help='Maximum time to wait for the SQL query to complete. See $ gcloud '
           'topic datetimes for information on duration formats.')

  msgs = apis.GetMessagesModule('spanner', 'v1')
  GetRequestPriorityMapper(msgs).choice_arg.AddToParser(parser)

  timestamp_bound_group = parser.add_argument_group(
      mutex=True,
      help='Read-only query timestamp bound. The default is --strong. See '
           'https://cloud.google.com/spanner/docs/timestamp-bounds.')
  timestamp_bound_group.add_argument(
      '--strong',
      action='store_true',
      help='Perform a strong query.')
  timestamp_bound_group.add_argument(
      '--read-timestamp',
      metavar='TIMESTAMP',
      help='Perform a query at the given timestamp.')
  parser.add_argument(
      '--database-role',
      help='Database role user assumes while accessing the database.')


def GetRequestPriorityMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--priority',
      messages.RequestOptions.PriorityValueValuesEnum,
      custom_mappings={
          'PRIORITY_LOW': 'low',
          'PRIORITY_MEDIUM': 'medium',
          'PRIORITY_HIGH': 'high',
          'PRIORITY_UNSPECIFIED': 'unspecified',
      },
      help_str='The priority for the execute SQL request.',
  )


@base.UnicodeIsSupported
class Query(base.Command):
  """Executes a SQL query against a Cloud Spanner database."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """See base class."""
    AddBaseArgs(parser)

  def Run(self, args):
    """Runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    msgs = apis.GetMessagesModule('spanner', 'v1')
    request_options = msgs.RequestOptions(
        priority=GetRequestPriorityMapper(msgs).GetEnumForChoice(args.priority)
    )
    read_only_options = self.ParseReadOnlyOptions(args)
    session = CreateSession(args, args.database_role)
    try:
      return database_sessions.ExecuteSql(
          args.sql,
          args.query_mode,
          session,
          read_only_options,
          request_options,
          args.enable_partitioned_dml,
          args.timeout)
    finally:
      database_sessions.Delete(session)

  def ParseReadOnlyOptions(self, args):
    """Parses the options for a read-only request from command line arguments.

    Args:
      args: Command line arguments.

    Returns:
      A ReadOnly message if the query is read-only (not DML), otherwise None.
    """
    if QueryHasDml(args.sql):
      if args.IsSpecified('strong'):
        raise c_exceptions.InvalidArgumentException(
            '--strong',
            'A timestamp bound cannot be specified for a DML statement.'
        )
      if args.IsSpecified('read_timestamp'):
        raise c_exceptions.InvalidArgumentException(
            '--read-timestamp',
            'A timestamp bound cannot be specified for a DML statement.'
        )
      return None
    else:
      msgs = apis.GetMessagesModule('spanner', 'v1')
      if args.IsSpecified('read_timestamp'):
        return msgs.ReadOnly(readTimestamp=args.read_timestamp)
      elif args.IsSpecified('strong'):
        if not args.strong:
          raise c_exceptions.InvalidArgumentException(
              '--strong',
              '`--strong` cannot be set to false. '
              'Instead specify a different type of timestamp bound.'
          )
        else:
          return msgs.ReadOnly(strong=True)
      else:
        # The default timestamp bound is strong.
        return msgs.ReadOnly(strong=True)

  def Display(self, args, result):
    """Displays the server response to a query.

    This is called higher up the stack to over-write default display behavior.
    What gets displayed depends on the mode in which the query was run.
    'NORMAL': query result rows
    'PLAN': query plan without execution statistics
    'PROFILE': query result rows and the query plan with execution statistics

    Args:
      args: The arguments originally passed to the command.
      result: The output of the command before display.

    Raises:
      ValueError: The query mode is not valid.
    """
    if args.query_mode == 'NORMAL':
      sql.DisplayQueryResults(result, log.out)
    elif args.query_mode == 'PLAN':
      sql.DisplayQueryPlan(result, log.out)
    elif args.query_mode == 'PROFILE':
      if sql.QueryHasAggregateStats(result):
        sql.DisplayQueryAggregateStats(result.stats.queryStats, log.out)
      sql.DisplayQueryPlan(result, log.out)
      sql.DisplayQueryResults(result, log.status)
    else:
      raise ValueError('Invalid query mode: {}'.format(args.query_mode))
