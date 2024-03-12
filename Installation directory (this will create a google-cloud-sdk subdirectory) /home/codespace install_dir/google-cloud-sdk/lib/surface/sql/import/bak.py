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
"""Imports data into a Cloud SQL instance from a BAK file.

Imports data into a Cloud SQL instance from a BAK backup file in Google Cloud
Storage.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import import_util
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Bak(base.Command):
  """Import data into a Cloud SQL instance from a BAK file."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
          {command} imports data into a Cloud SQL instance from a BAK backup
          file in Google Cloud Storage. You should use a full backup file with a
          single backup set.

          For detailed help on importing data into Cloud SQL, refer to this
          guide: https://cloud.google.com/sql/docs/sqlserver/import-export/importing
          """),
      'EXAMPLES':
          textwrap.dedent("""\
          To import data from the BAK file `my-bucket/my-export.bak` into the
          database `my-database` in the Cloud SQL instance `my-instance`,
          run:

            $ {command} my-instance gs://my-bucket/my-export.bak --database=my-database

          To import data from the encrypted BAK file `my-bucket/my-export.bak` into the database
          `my-database` in the Cloud SQL instance `my-instance`, with the certificate
          `gs://my-bucket/my-cert.crt`, private key `gs://my-bucket/my-key.key` and prompting for the
          private key password,
          run:

            $ {command} my-instance gs://my-bucket/my-export.bak --database=my-database --cert-path=gs://my-bucket/my-cert.crt --pvk-path=gs://my-bucket/my-key.key --prompt-for-pvk-password
          """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    import_util.AddBakImportFlags(
        parser, filetype='BAK file', gz_supported=False, user_supported=False
    )
    flags.AddDatabase(
        parser, flags.SQLSERVER_DATABASE_IMPORT_HELP_TEXT, required=True)
    flags.AddEncryptedBakFlags(parser)
    flags.AddBakImportStripedArgument(parser)
    flags.AddBakImportNoRecoveryArgument(parser)
    flags.AddBakImportRecoveryOnlyArgument(parser)
    flags.AddBakImportBakTypeArgument(parser)
    flags.AddBakImportStopAtArgument(parser)
    flags.AddBakImportStopAtMarkArgument(parser)

  def Run(self, args):
    """Runs the command to import into the Cloud SQL instance."""
    if args.prompt_for_pvk_password:
      args.pvk_password = console_io.PromptPassword('Private Key Password: ')

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    return import_util.RunBakImportCommand(args, client)
