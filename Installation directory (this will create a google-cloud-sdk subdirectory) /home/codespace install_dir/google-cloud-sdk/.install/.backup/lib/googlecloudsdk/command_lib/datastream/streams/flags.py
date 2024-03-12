# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Datastream related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


_MYSQL_EXCLUDED_OBJECTS_HELP_TEXT = """\
  Path to a YAML (or JSON) file containing the MySQL data sources to avoid backfilling.

  The JSON file is formatted as follows, with camelCase field naming:

  ```
    {
        "mysqlDatabases": [
            {
              "database":"sample_database",
              "mysqlTables": [
                {
                  "table": "sample_table",
                  "mysqlColumns": [
                    {
                      "column": "sample_column",
                    }
                   ]
                }
              ]
            }
          ]
        }
    }
  ```
"""

_ORACLE_EXCLUDED_OBJECTS_HELP_TEXT = """\
  Path to a YAML (or JSON) file containing the Oracle data sources to avoid backfilling.

  The JSON file is formatted as follows, with camelCase field naming:

  ```
    {
        "oracleSchemas": [
          {
            "schema": "SAMPLE",
            "oracleTables": [
              {
                "table": "SAMPLE_TABLE",
                "oracleColumns": [
                  {
                    "column": "COL",
                  }
                ]
              }
            ]
          }
        ]
      }
    }
  ```
"""
_POSTGRESQL_EXCLUDED_OBJECTS_HELP_TEXT = """\
  Path to a YAML (or JSON) file containing the PostgreSQL data sources to avoid backfilling.

  The JSON file is formatted as follows, with camelCase field naming:

  ```
    {
        "postgresqlSchemas": [
          {
            "schema": "SAMPLE",
            "postgresqlTables": [
              {
                "table": "SAMPLE_TABLE",
                "postgresqlColumns": [
                  {
                    "column": "COL",
                  }
                ]
              }
            ]
          }
        ]
      }
    }
  ```
"""


def AddDisplayNameFlag(parser, required=True):
  """Adds a --display-name flag to the given parser."""
  help_text = """Friendly name for the stream."""
  parser.add_argument('--display-name', help=help_text, required=required)


def AddUpdateMaskFlag(parser):
  """Adds a --update-mask flag to the given parser."""
  help_text = """Used to specify the fields to be overwritten in the stream resource by the update.
  If the update mask is used, then a field will be overwritten only if it is in the mask. If the user does not provide a mask then all fields will be overwritten.
  This is a comma-separated list of fully qualified names of fields, written as snake_case or camelCase. Example: "display_name, source_config.oracle_source_config"."""
  parser.add_argument('--update-mask', help=help_text)


def AddStateFlag(parser):
  """Adds a --state flag to the given parser."""
  help_text = """Stream state, can be set to: "RUNNING" or "PAUSED"."""
  parser.add_argument('--state', help=help_text)


def AddValidationGroup(parser, verb):
  """Adds a --validate-only or --force flag to the given parser."""
  validation_group = parser.add_group(mutex=True)
  validation_group.add_argument(
      '--validate-only',
      help="""Only validate the stream, but do not %s any resources.
      The default is false.""" % verb.lower(),
      action='store_true',
      default=False)
  validation_group.add_argument(
      '--force',
      help="""%s the stream without validating it.""" % verb,
      action='store_true',
      default=False)


def AddBackfillStrategyGroup(parser, required=True):
  """Adds a --backfiill-all or --backfill-none flag to the given parser."""
  backfill_group = parser.add_group(required=required, mutex=True)
  backfill_group.add_argument(
      '--backfill-none',
      help="""Do not automatically backfill any objects. This flag is equivalent
      to selecting the Manual backfill type in the Google Cloud console.""",
      action='store_true')
  backfill_all_group = backfill_group.add_group()
  backfill_all_group.add_argument(
      '--backfill-all',
      help="""Automatically backfill objects included in the stream source
      configuration. Specific objects can be excluded. This flag is equivalent
      to selecting the Automatic backfill type in the Google Cloud console.""",
      action='store_true')
  backfill_all_excluded_objects = backfill_all_group.add_group(mutex=True)
  backfill_all_excluded_objects.add_argument(
      '--oracle-excluded-objects', help=_ORACLE_EXCLUDED_OBJECTS_HELP_TEXT
  )
  backfill_all_excluded_objects.add_argument(
      '--mysql-excluded-objects', help=_MYSQL_EXCLUDED_OBJECTS_HELP_TEXT
  )
  backfill_all_excluded_objects.add_argument(
      '--postgresql-excluded-objects',
      help=_POSTGRESQL_EXCLUDED_OBJECTS_HELP_TEXT,
  )
