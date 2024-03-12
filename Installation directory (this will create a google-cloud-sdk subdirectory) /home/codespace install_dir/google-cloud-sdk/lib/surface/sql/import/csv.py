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
"""Imports data into a Cloud SQL instance from a CSV file.

Imports data into a Cloud SQL instance from a plain text file in a Google
Cloud Storage bucket with one line per row and comma-separated fields.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import import_util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Sql(base.Command):
  """Imports data into a Cloud SQL instance from a CSV file.

  Imports data into a Cloud SQL instance from a plain text file in a Google
  Cloud Storage bucket with one line per row and comma-separated fields.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    import_util.AddBaseImportFlags(parser, filetype='CSV')
    flags.AddDatabase(
        parser,
        'The database (for example, guestbook) to which the import is made.',
        required=True)
    parser.add_argument(
        '--table',
        required=True,
        help='The database table to import csv file into.')
    parser.add_argument(
        '--columns',
        required=False,
        type=arg_parsers.ArgList(min_length=1),
        metavar='COLUMNS',
        help='The columns to import from csv file. These correspond to actual '
        'database columns to import. If not set, all columns from csv file '
        'are imported to corresponding database columns.')
    flags.AddQuoteArgument(parser)
    flags.AddEscapeArgument(parser)
    flags.AddFieldsDelimiterArgument(parser)
    flags.AddLinesDelimiterArgument(parser)

  def Run(self, args):
    """Runs the command to import into the Cloud SQL instance."""
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    return import_util.RunCsvImportCommand(args, client)
