# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Export data from a Cloud SQL instance to a BAK file.

Export data from a Cloud SQL instance to a Google Cloud Storage bucket as
a BAK backup file.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import export_util
from googlecloudsdk.command_lib.sql import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Bak(base.Command):
  """Export data from a Cloud SQL instance to a BAK file.

  Export data from a Cloud SQL instance to a Google Cloud Storage
  bucket as a BAK backup file. This is only supported for SQL Server.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To export data from the database `my-database` in the Cloud SQL
          instance `my-instance` to a BAK file `my-bucket/my-export.bak`,
          run:

            $ {command} my-instance gs://my-bucket/my-export.bak --database=my-database
          """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    export_util.AddBaseExportFlags(
        parser,
        gz_supported=False,
        database_required=True,
        database_help_text=flags.SQLSERVER_DATABASE_LIST_EXPORT_HELP_TEXT)
    flags.AddBakExportStripeCountArgument(parser)
    flags.AddBakExportStripedArgument(parser)
    flags.AddBakExportBakTypeArgument(parser)
    flags.AddBakExportDifferentialBaseArgument(parser)

  def Run(self, args):
    """Runs the command to export the Cloud SQL instance."""
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    return export_util.RunBakExportCommand(args, client)
