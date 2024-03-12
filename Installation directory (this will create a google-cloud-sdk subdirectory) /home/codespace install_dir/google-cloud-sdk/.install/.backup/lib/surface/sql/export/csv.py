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
"""Exports data from a Cloud SQL instance to a CSV file.

Exports data from a Cloud SQL instance to a Google Cloud Storage bucket as a
plain text file with one line per row and comma-separated fields.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import export_util
from googlecloudsdk.command_lib.sql import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Csv(base.Command):
  """Exports data from a Cloud SQL instance to a CSV file.

  Exports data from a Cloud SQL instance to a Google Cloud Storage bucket as a
  plain text file with one line per row and comma-separated fields.
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
    parser.add_argument(
        '--query',
        required=True,
        help='A SQL SELECT query (e.g., SELECT * FROM table) that specifies '
             'the data to export. WARNING: While in-transit, the query might '
             'be processed in intermediate locations other than the location '
             'of the target instance.')
    flags.AddQuoteArgument(parser)
    flags.AddEscapeArgument(parser)
    flags.AddFieldsDelimiterArgument(parser)
    flags.AddLinesDelimiterArgument(parser)

  def Run(self, args):
    """Runs the command to export the Cloud SQL instance."""
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    return export_util.RunCsvExportCommand(args, client)
