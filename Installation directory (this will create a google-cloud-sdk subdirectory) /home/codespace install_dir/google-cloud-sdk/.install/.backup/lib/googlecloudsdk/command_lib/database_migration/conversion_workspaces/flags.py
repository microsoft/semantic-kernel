# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the conversion workspace related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AddNoAsyncFlag(parser):
  """Adds a --no-async flag to the given parser."""
  help_text = (
      'Waits for the operation in progress to complete before returning.'
  )
  parser.add_argument('--no-async', action='store_true', help=help_text)


def AddDisplayNameFlag(parser):
  """Adds a --display-name flag to the given parser."""
  help_text = """
    A user-friendly name for the conversion workspace. The display name can
    include letters, numbers, spaces, and hyphens, and must start with a letter.
    The maximum length allowed is 60 characters.
    """
  parser.add_argument('--display-name', help=help_text)


def AddDatabaseEngineFlag(parser):
  """Adds the --source-database-engine and --destination-database-engine flags to the given parser."""
  help_text = """\
    Database engine type.
    """
  # TODO(b/276653183): Add mysql and spanner choices once mysql to spanner is
  # supported.
  source_choices = ['ORACLE']
  destination_choices = ['POSTGRESQL']

  parser.add_argument(
      '--source-database-engine',
      help=help_text,
      choices=source_choices,
      required=True,
  )

  parser.add_argument(
      '--destination-database-engine',
      help=help_text,
      choices=destination_choices,
      required=True,
  )


def AddDatabaseVersionFlag(parser):
  """Adds the --source-database-version and --destination-database-version flags to the given parser."""
  help_text = """
    Version number for the database engine. The version number must contain numbers and letters only. Example for Oracle 21c, version number will be 21c.
    """
  parser.add_argument(
      '--source-database-version', help=help_text, required=True
  )
  parser.add_argument(
      '--destination-database-version', help=help_text, required=True
  )


def AddGlobalSettingsFlag(parser):
  """Adds a --global-settings flag to the given parser."""
  help_text = """\
    A generic list of settings for the workspace. The settings are database pair
    dependant and can indicate default behavior for the mapping rules engine or
    turn on or off specific features. An object containing a list of
    "key": "value" pairs.
    """
  parser.add_argument(
      '--global-settings',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text,
  )


def AddCommitNameFlag(parser):
  """Adds a --commit-name flag to the given parser."""
  help_text = """
    A user-friendly name for the conversion workspace commit. The commit name
    can include letters, numbers, spaces, and hyphens, and must start with a
    letter.
    """
  parser.add_argument('--commit-name', help=help_text)


def AddAutoCommitFlag(parser):
  """Adds a --auto-commit flag to the given parser."""
  help_text = 'Auto commits the conversion workspace.'
  parser.add_argument('--auto-commit', action='store_true', help=help_text)


def AddImportFileFormatFlag(parser):
  """Adds the --file-format flag to the given parser."""
  help_text = """\
    File format type to import rules from.
    """
  # TODO(b/276653183): Add harbour bridge choice once mysql to spanner is
  # supported.
  choices = ['ORA2PG']

  parser.add_argument(
      '--file-format', help=help_text, choices=choices, required=True
  )


def AddConfigFilesFlag(parser):
  """Adds a --config-files flag to the given parser."""
  help_text = """\
    A list of files to import rules from. Either provide a single file path or if
    multiple files are to be provided, each file should correspond to one schema.
    Provide file paths as a comma separated list.
    """
  parser.add_argument(
      '--config-files',
      metavar='CONGIF_FILE',
      type=arg_parsers.ArgList(min_length=1),
      help=help_text,
      required=True,
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


def AddTreeTypeFlag(parser, required=True, default_value='DRAFT'):
  """Adds the --tree-type flag to the given parser."""
  help_text = """\
    Tree type for database entities.
    """
  choices = ['SOURCE', 'DRAFT']

  parser.add_argument(
      '--tree-type',
      help=help_text,
      choices=choices,
      required=required,
      default=default_value,
  )


def AddUncomittedFlag(parser):
  """Adds a --uncommitted flag to the given parser."""
  help_text = (
      'Whether to retrieve the latest committed version of the entities or the'
      ' latest version. This field is ignored if a specific commit_id is'
      ' specified.'
  )
  parser.add_argument('--uncommitted', action='store_true', help=help_text)


def AddCommitIdFlag(parser):
  """Adds a --commit-id flag to the given parser."""
  help_text = (
      'Request a specific commit id. If not specified, the entities from the'
      ' latest commit are returned.'
  )
  parser.add_argument('--commit-id', help=help_text)
