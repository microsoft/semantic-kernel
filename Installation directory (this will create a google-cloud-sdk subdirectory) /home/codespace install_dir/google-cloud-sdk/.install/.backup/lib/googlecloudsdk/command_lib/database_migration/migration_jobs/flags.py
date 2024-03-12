# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the migration jobs related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.calliope import arg_parsers


@enum.unique
class ApiType(enum.Enum):
  """This API type is used to differentiate between the classification types of Create requests and Update requests."""
  CREATE = 'create'
  UPDATE = 'update'


def AddNoAsyncFlag(parser):
  """Adds a --no-async flag to the given parser."""
  help_text = (
      'Waits for the operation in progress to complete before returning.'
  )
  parser.add_argument('--no-async', action='store_true', help=help_text)


def AddDisplayNameFlag(parser):
  """Adds a --display-name flag to the given parser."""
  help_text = """
    A user-friendly name for the migration job. The display name can include
    letters, numbers, spaces, and hyphens, and must start with a letter.
    """
  parser.add_argument('--display-name', help=help_text)


def AddTypeFlag(parser, required=False):
  """Adds --type flag to the given parser."""
  help_text = 'Type of the migration job.'
  choices = ['ONE_TIME', 'CONTINUOUS']
  parser.add_argument(
      '--type', help=help_text, choices=choices, required=required
  )


def AddDumpPathFlag(parser):
  """Adds a --dump-path flag to the given parser."""
  help_text = """\
    Path to the dump file in Google Cloud Storage, in the format:
    `gs://[BUCKET_NAME]/[OBJECT_NAME]`.
    """
  parser.add_argument('--dump-path', help=help_text)


def AddConnectivityGroupFlag(parser, api_type, required=False):
  """Adds connectivity flag group to the given parser."""
  if api_type == ApiType.CREATE:
    connectivity_group = parser.add_group(
        (
            'The connectivity method used by the migration job. If a'
            " connectivity method isn't specified, then it isn't added to the"
            ' migration job.'
        ),
        mutex=True,
    )
  elif api_type == ApiType.UPDATE:
    connectivity_group = parser.add_group(
        (
            'The connectivity method used by the migration job. If a'
            " connectivity method isn't specified, then it isn't updated for"
            ' the migration job.'
        ),
        mutex=True,
    )
  connectivity_group.add_argument(
      '--static-ip',
      action='store_true',
      help=(
          'Use the default IP allowlist method. This method creates a public IP'
          ' that will be used with the destination Cloud SQL database. The'
          ' method works by configuring the source database server to accept'
          ' connections from the outgoing IP of the Cloud SQL instance.'
      ),
  )
  connectivity_group.add_argument(
      '--peer-vpc',
      help=(
          'Name of the VPC network to peer with the Cloud SQL private network.'
      ),
  )
  reverse_ssh_group = connectivity_group.add_group(
      'Parameters for the reverse-SSH tunnel connectivity method.'
  )
  reverse_ssh_group.add_argument(
      '--vm-ip', help='Bastion Virtual Machine IP.', required=required
  )
  reverse_ssh_group.add_argument(
      '--vm-port',
      help='Forwarding port for the SSH tunnel.',
      type=int,
      required=required,
  )
  reverse_ssh_group.add_argument(
      '--vm', help='Name of VM that will host the SSH tunnel bastion.'
  )
  reverse_ssh_group.add_argument(
      '--vpc',
      help='Name of the VPC network where the VM is hosted.',
      required=required,
  )


def AddFilterFlag(parser):
  """Adds a --filter flag to the given parser."""
  help_text = (
      'Filter the entities based on [AIP-160](https://google.aip.dev/160)'
      ' standard. Example: to filter all tables whose name start with'
      ' "Employee" and are present under schema "Company", use filter as'
      ' "Company.Employee```*``` AND type=TABLE"'
  )
  parser.add_argument('--filter', help=help_text)


def AddCommitIdFlag(parser):
  """Adds a --commit-id flag to the given parser."""
  help_text = (
      'Commit id for the conversion workspace to use for creating the migration'
      ' job. If not specified, the latest commit id will be used by default.'
  )
  parser.add_argument('--commit-id', help=help_text)


def AddDumpParallelLevelFlag(parser):
  """Adds a --dump-parallel-level flag to the given parser."""
  help_text = (
      'Parallelization level during initial dump of the migration job. If not'
      ' specified, will be defaulted to OPTIMAL.'
  )
  choices = ['MIN', 'OPTIMAL', 'MAX']
  parser.add_argument('--dump-parallel-level', help=help_text, choices=choices)


def AddDumpTypeFlag(parser):
  """Adds a --dump-type flag to the given parser."""
  help_text = (
      'The type of the data dump. Currently applicable for MySQL to MySQL '
      'migrations only.'
  )
  choices = ['LOGICAL', 'PHYSICAL']
  parser.add_argument(
      '--dump-type', help=help_text, choices=choices, hidden=True
  )


def AddSqlServerHomogeneousMigrationConfigFlag(parser):
  """Adds SQL Server homogeneous migration flag group to the given parser."""
  sqlserver_homogeneous_migration_config = parser.add_group(
      (
          'The SQL Server homogeneous migration config. This is used only for'
          ' SQL Server to CloudSQL SQL Server migrations.'
      ),
      hidden=True,
  )
  AddSqlServerBackupFilePattern(sqlserver_homogeneous_migration_config)
  AddSqlServerDatabasesFlag(sqlserver_homogeneous_migration_config)
  AddSqlServerEncryptedDatabasesFlag(sqlserver_homogeneous_migration_config)


def AddSqlServerBackupFilePattern(parser):
  """Adds a --sqlserver-backup-file-pattern flag to the given parser."""
  help_text = (
      'Pattern that describes the default backup naming strategy. The specified'
      ' pattern should ensure lexicographical order of backups. The pattern'
      ' must define one of the following capture group sets:\nCapture group set'
      ' #1\nyy/yyyy - year, 2 or 4 digits mm - month number, 1-12 dd - day of'
      ' month,1-31 hh - hour of day, 00-23 mi - minutes, 00-59 ss - seconds,'
      ' 00-59\nExample: For backup file TestDB_backup_20230802_155400.trn, use'
      ' pattern:(?<database>.*)_backup_(?<yyyy>\\d{4})(?<mm>\\d{2})(?<dd>\\d{2})_(?<hh>\\d{2})(?<mi>\\d{2})(?<ss>\\d{2}).trn'
      ' \nCapture group set #2\ntimestamp - unix timestamp\nExample: For backup'
      ' file TestDB_backup_1691448254.trn, use'
      ' pattern:(?<database>.*)_backup_(?<timestamp>.*).trn'
  )
  parser.add_argument(
      '--sqlserver-backup-file-pattern',
      help=help_text,
      default='(?<database>.*)_(?<yyyy>\\d{4})(?<mm>\\d{2})(?<dd>\\d{2})_(?<hh>\\d{2})(?<mi>\\d{2})(?<ss>\\d{2})_(full|log)\\.(trn|bak)',
  )


def AddSqlServerDatabasesFlag(parser):
  """Adds a --sqlserver-databases flag to the given parser."""
  help_text = """\
    A list of databases to be migrated to the destination Cloud SQL instance.
    Provide databases as a comma separated list. This list should contain all
    encrypted and non-encrypted database names.
    """
  parser.add_argument(
      '--sqlserver-databases',
      metavar='databaseName',
      type=arg_parsers.ArgList(min_length=1),
      help=help_text,
      required=True,
  )


def AddSqlServerEncryptedDatabasesFlag(parser):
  """Adds a --sqlserver-encrypted-databases flag to the given parser."""
  help_text = """\
    A JSON/YAML file describing the encryption settings per database for all encrytped databases.
    An example of a JSON request:
        [{
            "databaseName": "db1",
            "databaseDetails": {
                "encryptionOptions": {
                    "certPath": "Path to certificate 1",
                    "pvkPath": "Path to certificate private key 1",
                    "pvkPassword": "Private key password 1"
                }
            }
        },
        {
            "databaseName": "db2",
            "databaseDetails": {
                "encryptionOptions": {
                    "certPath": "Path to certificate 2",
                    "pvkPath": "Path to certificate private key 2",
                    "pvkPassword": "Private key password 2"
                }
            }
        }]

      This flag accepts "-" for stdin.
    """
  parser.add_argument(
      '--sqlserver-encrypted-databases',
      type=arg_parsers.YAMLFileContents(),
      help=help_text,
  )
