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
"""Flags and helpers for the connection profiles related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util


def AddNoAsyncFlag(parser):
  """Adds a --no-async flag to the given parser."""
  help_text = ('Waits for the operation in progress to complete before '
               'returning.')
  parser.add_argument('--no-async', action='store_true', help=help_text)


def AddDisplayNameFlag(parser):
  """Adds a --display-name flag to the given parser."""
  help_text = """\
    A user-friendly name for the connection profile. The display name can
    include letters, numbers, spaces, and hyphens, and must start with a letter.
    """
  parser.add_argument('--display-name', help=help_text)


def AddDatabaseParamsFlags(parser, require_password=True):
  """Adds the database connectivity flags to the given parser."""

  database_params_group = parser.add_group(required=False, mutex=False)
  AddUsernameFlag(database_params_group, required=True)
  AddPasswordFlagGroup(database_params_group, required=require_password)
  AddHostFlag(database_params_group, required=True)
  AddPortFlag(database_params_group, required=True)


def AddUsernameFlag(parser, required=False):
  """Adds a --username flag to the given parser."""
  help_text = """\
    Username that Database Migration Service uses to connect to the
    database. Database Migration Service encrypts the value when storing it.
    """
  parser.add_argument('--username', help=help_text, required=required)


def AddPasswordFlagGroup(parser, required=False):
  """Adds --password and --prompt-for-password flags to the given parser."""

  password_group = parser.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--password',
      help="""\
          Password for the user that Database Migration Service uses to
          connect to the database. Database Migration Service encrypts
          the value when storing it, and the field is not returned on request.
          """)
  password_group.add_argument(
      '--prompt-for-password',
      action='store_true',
      help='Prompt for the password used to connect to the database.')


def AddHostFlag(parser, required=False):
  """Adds --host flag to the given parser."""
  help_text = """\
    IP or hostname of the database.
    When `--psc-service-attachment` is also specified, this field value should be:
    1. For Cloud SQL PSC enabled instance - the dns_name field (e.g <uid>.<region>.sql.goog.).
    2. For Cloud SQL PSA instance (vpc peering) - the private ip of the instance.
  """
  parser.add_argument('--host', help=help_text, required=required)


def AddPortFlag(parser, required=False):
  """Adds --port flag to the given parser."""
  help_text = """\
    Network port of the database.
  """
  parser.add_argument('--port', help=help_text, required=required, type=int)


def AddSslConfigGroup(parser, release_track):
  """Adds ssl server only & server client config group to the given parser."""
  ssl_config = parser.add_group()
  AddCaCertificateFlag(ssl_config, True)
  client_cert = ssl_config.add_group()
  AddPrivateKeyFlag(client_cert, required=True)
  if api_util.GetApiVersion(release_track) == 'v1alpha2':
    AddCertificateFlag(client_cert, required=True)
  else:
    AddClientCertificateFlag(client_cert, required=True)


def AddSslServerOnlyConfigGroup(parser):
  """Adds ssl server only config group to the given parser."""
  ssl_config = parser.add_group()
  AddCaCertificateFlag(ssl_config, True)


def AddCaCertificateFlag(parser, required=False):
  """Adds --ca-certificate flag to the given parser."""
  help_text = """\
    x509 PEM-encoded certificate of the CA that signed the database
    server's certificate. Database Migration Service will use this certificate to verify
    it's connecting to the correct host. Database Migration Service encrypts the
    value when storing it.
  """
  parser.add_argument('--ca-certificate', help=help_text, required=required)


def AddCertificateFlag(parser, required=False):
  """Adds --certificate flag to the given parser."""
  help_text = """\
    x509 PEM-encoded certificate that will be used by the replica to
    authenticate against the database server.
  """
  parser.add_argument('--certificate', help=help_text, required=required)


def AddClientCertificateFlag(parser, required=False):
  """Adds --client-certificate flag to the given parser."""
  help_text = """\
    x509 PEM-encoded certificate that will be used by the replica to
    authenticate against the database server. Database Migration Service
    encrypts the value when storing it.
  """
  parser.add_argument('--client-certificate', help=help_text, required=required)


def AddPrivateKeyFlag(parser, required=False):
  """Adds --private-key flag to the given parser."""
  help_text = """\
    Unencrypted PKCS#1 or PKCS#8 PEM-encoded private key associated with
    the Client Certificate. Database Migration Service encrypts the value when
    storing it.
  """
  parser.add_argument('--private-key', help=help_text, required=required)


def AddInstanceFlag(parser, required=False):
  """Adds --instance flag to the given parser."""
  help_text = """\
    If the source is a Cloud SQL database, use this field to provide the Cloud
    SQL instance ID of the source.
  """
  parser.add_argument('--instance', help=help_text, required=required)


def AddCloudSQLInstanceFlag(parser, required=False):
  """Adds --cloudsql-instance flag to the given parser."""
  help_text = """\
    If the source or destination is a Cloud SQL database, then use this field
    to provide the respective Cloud SQL instance ID.
  """
  parser.add_argument('--cloudsql-instance', help=help_text, required=required)


def AddAlloydbClusterFlag(parser, required=False):
  """Adds the --alloydb-cluster flag to the given parser."""
  help_text = """\
    If the destination is an AlloyDB cluster, use this field to provide the
    AlloyDB cluster ID.
  """
  parser.add_argument('--alloydb-cluster', help=help_text, required=required)


def AddProviderFlag(parser):
  """Adds --provider flag to the given parser."""
  help_text = """\
    Database provider, for managed databases.
  """
  choices = ['RDS', 'CLOUDSQL']
  parser.add_argument('--provider', help=help_text, choices=choices)
