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
"""Exports data from a Cloud SQL instance to a SQL file.

Exports data from a Cloud SQL instance to a Google Cloud Storage bucket as
a SQL dump file.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import export_util
from googlecloudsdk.command_lib.sql import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Sql(base.Command):
  # pylint: disable=line-too-long
  """Exports data from a Cloud SQL instance to a SQL file.

  Exports data from a Cloud SQL instance to a Google Cloud Storage
  bucket as a SQL dump file.

  NOTE: Certain roles and permissions are required to export data to Google
  Cloud Storage. For more information on exporting data from Google Cloud SQL
  see [Export from Cloud SQL to a SQL dump file](https://cloud.google.com/sql/docs/mysql/import-export/import-export-sql#gcloud).
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    export_util.AddBaseExportFlags(parser)
    flags.AddOffloadArgument(parser)
    flags.AddParallelArgument(parser, operation='export')
    flags.AddThreadsArgument(parser, operation='export')
    parser.add_argument(
        '--table',
        '-t',
        type=arg_parsers.ArgList(min_length=1),
        metavar='TABLE',
        required=False,
        help='Tables to export from the specified database. If you specify '
        'tables, specify one and only one database. For PostgreSQL instances, '
        'only one table can be exported at a time.')

  def Run(self, args):
    """Runs the command to export the Cloud SQL instance."""
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    return export_util.RunSqlExportCommand(args, client)
