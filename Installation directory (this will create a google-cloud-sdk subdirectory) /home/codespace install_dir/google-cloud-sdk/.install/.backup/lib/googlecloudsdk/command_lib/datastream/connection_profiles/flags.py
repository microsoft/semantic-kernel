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
"""Flags and helpers for the Datastream related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base


def AddTypeFlag(parser):
  """Adds a --type flag to the given parser."""
  help_text = """Type can be MYSQL, ORACLE, POSTGRESQL, GOOGLE-CLOUD-STORAGE or BIGQUERY"""

  parser.add_argument('--type', help=help_text, required=True)


def AddDisplayNameFlag(parser, required=True):
  """Adds a --display-name flag to the given parser."""
  help_text = """Friendly name for the connection profile."""
  parser.add_argument('--display-name', help=help_text, required=required)


def AddMysqlProfileGroup(parser, required=True):
  """Adds necessary mysql profile flags to the given parser."""
  mysql_profile = parser.add_group()
  mysql_profile.add_argument(
      '--mysql-hostname',
      help="""IP or hostname of the MySQL source database.""",
      required=required)
  mysql_profile.add_argument(
      '--mysql-port',
      help="""Network port of the MySQL source database.""",
      required=required,
      type=int)
  mysql_profile.add_argument(
      '--mysql-username',
      help="""Username Datastream will use to connect to the database.""",
      required=required)
  password_group = mysql_profile.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--mysql-password',
      help="""\
          Password for the user that Datastream will be using to
          connect to the database.
          This field is not returned on request, and the value is encrypted
          when stored in Datastream.""")
  password_group.add_argument(
      '--mysql-prompt-for-password',
      action='store_true',
      help='Prompt for the password used to connect to the database.')
  ssl_config = mysql_profile.add_group()
  ssl_config.add_argument(
      '--ca-certificate',
      help="""\
          x509 PEM-encoded certificate of the CA that signed the source database
          server's certificate. The replica will use this certificate to verify
          it's connecting to the right host.""",
      required=required)
  ssl_config.add_argument(
      '--client-certificate',
      help="""\
          x509 PEM-encoded certificate that will be used by the replica to
          authenticate against the source database server.""",
      required=required)
  ssl_config.add_argument(
      '--client-key',
      help="""\
          Unencrypted PKCS#1 or PKCS#8 PEM-encoded private key associated with
          the Client Certificate.""",
      required=required)


def AddOracleProfileGroup(parser, required=True):
  """Adds necessary oracle profile flags to the given parser."""
  oracle_profile = parser.add_group()
  oracle_profile.add_argument(
      '--oracle-hostname',
      help="""IP or hostname of the oracle source database.""",
      required=required)
  oracle_profile.add_argument(
      '--oracle-port',
      help="""Network port of the oracle source database.""",
      required=required,
      type=int)
  oracle_profile.add_argument(
      '--oracle-username',
      help="""Username Datastream will use to connect to the database.""",
      required=required)
  oracle_profile.add_argument(
      '--database-service',
      help="""Database service for the Oracle connection.""",
      required=required)
  password_group = oracle_profile.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--oracle-password',
      help="""\
          Password for the user that Datastream will be using to
          connect to the database.
          This field is not returned on request, and the value is encrypted
          when stored in Datastream.""")
  password_group.add_argument(
      '--oracle-prompt-for-password',
      action='store_true',
      help='Prompt for the password used to connect to the database.')


def AddPostgresqlProfileGroup(parser, required=True):
  """Adds necessary postgresql profile flags to the given parser."""
  postgresql_profile = parser.add_group()
  postgresql_profile.add_argument(
      '--postgresql-hostname',
      help="""IP or hostname of the PostgreSQL source database.""",
      required=required)
  postgresql_profile.add_argument(
      '--postgresql-port',
      help="""Network port of the PostgreSQL source database.""",
      required=required,
      type=int)
  postgresql_profile.add_argument(
      '--postgresql-username',
      help="""Username Datastream will use to connect to the database.""",
      required=required)
  postgresql_profile.add_argument(
      '--postgresql-database',
      help="""Database service for the PostgreSQL connection.""",
      required=required)
  password_group = postgresql_profile.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--postgresql-password',
      help="""\
          Password for the user that Datastream will be using to
          connect to the database.
          This field is not returned on request, and the value is encrypted
          when stored in Datastream.""")
  password_group.add_argument(
      '--postgresql-prompt-for-password',
      action='store_true',
      help='Prompt for the password used to connect to the database.')


def AddGcsProfileGroup(parser, release_track, required=True):
  """Adds necessary GCS profile flags to the given parser."""
  gcs_profile = parser.add_group()

  bucket_field_name = '--bucket'
  if release_track == base.ReleaseTrack.BETA:
    bucket_field_name = '--bucket-name'

  gcs_profile.add_argument(
      bucket_field_name,
      help="""The full project and resource path for Cloud Storage
      bucket including the name.""",
      required=required)

  gcs_profile.add_argument(
      '--root-path',
      help="""The root path inside the Cloud Storage bucket.""",
      required=False)


def AddDepthGroup(parser):
  """Adds necessary depth flags for discover command parser."""
  depth_parser = parser.add_group(mutex=True)
  depth_parser.add_argument(
      '--recursive',
      help="""Whether to retrieve the full hierarchy of data objects (TRUE) or only the current level (FALSE).""",
      action=actions.DeprecationAction(
          '--recursive',
          warn=(
              'The {flag_name} option is deprecated; use `--full-hierarchy`'
              ' instead.'
          ),
          removed=False,
          action='store_true',
      ),
  )
  depth_parser.add_argument(
      '--recursive-depth',
      help="""The number of hierarchy levels below the current level to be retrieved.""",
      action=actions.DeprecationAction(
          '--recursive-depth',
          warn=(
              'The {flag_name} option is deprecated; use `--hierarchy-depth`'
              ' instead.'
          ),
          removed=False,
      ),
  )


def AddHierarchyGroup(parser):
  """Adds necessary hierarchy flags for discover command parser."""
  hierarchy_parser = parser.add_group(mutex=True)
  hierarchy_parser.add_argument(
      '--full-hierarchy',
      help="""Whether to retrieve the full hierarchy of data objects (TRUE) or only the current level (FALSE).""",
      action='store_true',
  )

  hierarchy_parser.add_argument(
      '--hierarchy-depth',
      help="""The number of hierarchy levels below the current level to be retrieved.""",
  )


def AddRdbmsGroup(parser):
  """Adds necessary RDBMS params for discover command parser."""
  rdbms_parser = parser.add_group(mutex=True)
  rdbms_parser.add_argument(
      '--mysql-rdbms-file',
      help="""Path to a YAML (or JSON) file containing the MySQL RDBMS to enrich with child data objects and metadata. If you pass - as the value of the flag the file content will be read from stdin. """
  )
  rdbms_parser.add_argument(
      '--oracle-rdbms-file',
      help="""Path to a YAML (or JSON) file containing the Oracle RDBMS to enrich with child data objects and metadata. If you pass - as the value of the flag the file content will be read from stdin."""
  )
  rdbms_parser.add_argument(
      '--postgresql-rdbms-file',
      help="""Path to a YAML (or JSON) file containing the PostgreSQL RDBMS to enrich with child data objects and metadata. If you pass - as the value of the flag the file content will be read from stdin."""
  )


def AddValidationGroup(parser, verb):
  """Adds a --force flag to the given parser."""
  validation_group = parser.add_group(mutex=True)
  validation_group.add_argument(
      '--force',
      help="""%s the connection profile without validating it.""" % verb,
      action='store_true',
      default=False)
