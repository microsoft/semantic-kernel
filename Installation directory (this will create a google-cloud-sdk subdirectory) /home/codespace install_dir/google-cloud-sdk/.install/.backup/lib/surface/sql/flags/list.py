# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Lists customizable flags for Google Cloud SQL instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


def _AddCommonFlags(parser):
  """Adds flags common to all release tracks."""
  parser.display_info.AddFormat("""
    table(
        name,
        type,
        appliesTo.list():label=DATABASE_VERSION,
        allowedStringValues.list():label=ALLOWED_VALUES
      )
    """)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List customizable flags for Google Cloud SQL instances."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    _AddCommonFlags(parser)
    flags.AddDatabaseVersion(parser)

  def Run(self, args):
    """List customizable flags for Google Cloud SQL instances.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
      with.

    Returns:
      A dict object that has the list of flag resources if the command ran
      successfully.
    """

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    result = sql_client.flags.List(
        sql_messages.SqlFlagsListRequest(databaseVersion=args.database_version))
    return iter(result.items)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListAlphaBeta(List):
  """List customizable flags for Google Cloud SQL instances."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    _AddCommonFlags(parser)
    flags.AddDatabaseVersion(parser, restrict_choices=False)
