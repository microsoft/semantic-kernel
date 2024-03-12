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
"""Command to create Cloud Firestore Database in Native mode."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import api_utils
from googlecloudsdk.api_lib.firestore import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(
    base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class CreateFirestoreAPI(base.Command):
  """Create a Google Cloud Firestore database via Firestore API.

  ## EXAMPLES

  To create a Firestore Native database in `nam5`.

      $ {command} --location=nam5

  To create a Datastore Mode database in `us-east1`.

      $ {command} --location=us-east1 --type=datastore-mode

  To create a Datastore Mode database in `us-east1` with a databaseId `foo`.

      $ {command} --database=foo --location=us-east1 --type=datastore-mode

  To create a Firestore Native database in `nam5` with delete protection
  enabled.

      $ {command} --location=nam5 --delete-protection

  To create a Firestore Native database in `nam5` with Point In Time Recovery
  (PITR) enabled.

      $ {command} --location=nam5 --enable-pitr
  """

  def DatabaseType(self, database_type):
    if database_type == 'firestore-native':
      return (
          api_utils.GetMessages().GoogleFirestoreAdminV1Database.TypeValueValuesEnum.FIRESTORE_NATIVE
      )
    elif database_type == 'datastore-mode':
      return (
          api_utils.GetMessages().GoogleFirestoreAdminV1Database.TypeValueValuesEnum.DATASTORE_MODE
      )
    else:
      raise ValueError('invalid database type: {}'.format(database_type))

  def DatabaseDeleteProtectionState(self, enable_delete_protection):
    if enable_delete_protection:
      return (
          api_utils.GetMessages().GoogleFirestoreAdminV1Database.DeleteProtectionStateValueValuesEnum.DELETE_PROTECTION_ENABLED
      )
    return (
        api_utils.GetMessages().GoogleFirestoreAdminV1Database.DeleteProtectionStateValueValuesEnum.DELETE_PROTECTION_DISABLED
    )

  def DatabasePitrState(self, enable_pitr):
    if enable_pitr is None:
      return (
          api_utils.GetMessages().GoogleFirestoreAdminV1Database.PointInTimeRecoveryEnablementValueValuesEnum.POINT_IN_TIME_RECOVERY_ENABLEMENT_UNSPECIFIED
      )
    if enable_pitr:
      return (
          api_utils.GetMessages().GoogleFirestoreAdminV1Database.PointInTimeRecoveryEnablementValueValuesEnum.POINT_IN_TIME_RECOVERY_ENABLED
      )
    return (
        api_utils.GetMessages().GoogleFirestoreAdminV1Database.PointInTimeRecoveryEnablementValueValuesEnum.POINT_IN_TIME_RECOVERY_DISABLED
    )

  def DatabaseCmekConfig(self, args):
    return (
        api_utils.GetMessages().GoogleFirestoreAdminV1CmekConfig()
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return databases.CreateDatabase(
        project,
        args.location,
        args.database,
        self.DatabaseType(args.type),
        self.DatabaseDeleteProtectionState(args.delete_protection),
        self.DatabasePitrState(args.enable_pitr),
        self.DatabaseCmekConfig(args),
    )

  @classmethod
  def Args(cls, parser):
    flags.AddLocationFlag(
        parser, required=True, suggestion_aliases=['--region']
    )
    parser.add_argument(
        '--type',
        help='The type of the database.',
        default='firestore-native',
        choices=['firestore-native', 'datastore-mode'],
    )
    parser.add_argument(
        '--database',
        help="""The ID to use for the database, which will become the final
        component of the database's resource name. If database ID is not
        provided, (default) will be used as database ID.

        This value should be 4-63 characters. Valid characters are /[a-z][0-9]-/
        with first character a letter and the last a letter or a number. Must
        not be UUID-like /[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/.

        Using "(default)" database ID is also allowed.
        """,
        type=str,
        default='(default)',
    )
    parser.add_argument(
        '--delete-protection',
        help="""Whether to enable delete protection on the created database.

        If set to true, delete protection of the new database will be enabled
        and delete operations will fail unless delete protection is disabled.

        Default to false.
        """,
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--enable-pitr',
        help="""Whether to enable Point In Time Recovery (PITR) on the created
        database.

        If set to true, PITR on the new database will be enabled. By default,
        this feature is not enabled.
        """,
        action='store_true',
        default=None,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateFirestoreAPIWithCmekConfig(CreateFirestoreAPI):
  r"""Create a Google Cloud Firestore database via Firestore API.

  ## EXAMPLES

  To create a Firestore Native database in `nam5`.

      $ {command} --location=nam5

  To create a Datastore Mode database in `us-east1`.

      $ {command} --location=us-east1 --type=datastore-mode

  To create a Datastore Mode database in `us-east1` with a databaseId `foo`.

      $ {command} --database=foo --location=us-east1 --type=datastore-mode

  To create a Firestore Native database in `nam5` with delete protection
  enabled.

      $ {command} --location=nam5 --delete-protection

  To create a Firestore Native database in `nam5` with Point In Time Recovery
  (PITR) enabled.

      $ {command} --location=nam5 --enable-pitr
  """

  def DatabaseCmekConfig(self, args):
    if args.kms_key_name is not None:
      return api_utils.GetMessages().GoogleFirestoreAdminV1CmekConfig(
          kmsKeyName=args.kms_key_name
      )
    return api_utils.GetMessages().GoogleFirestoreAdminV1CmekConfig()

  @classmethod
  def Args(cls, parser):
    super(CreateFirestoreAPIWithCmekConfig, cls).Args(parser)
    parser.add_argument(
        '--kms-key-name',
        help="""The resource ID of a Cloud KMS key. If set, the database created will
        be a Customer-managed Encryption Key (CMEK) database encrypted with
        this key. This feature is allowlist only in initial launch.

        Only the key in the same location as this database is allowed to be
        used for encryption.

        For Firestore's nam5 multi-region, this corresponds to Cloud KMS
        location us. For Firestore's eur3 multi-region, this corresponds to
        Cloud KMS location europe. See https://cloud.google.com/kms/docs/locations.

        This value should be the KMS key resource ID in the format of
        `projects/{project_id}/locations/{kms_location}/keyRings/{key_ring}/cryptoKeys/{crypto_key}`.
        How to retrive this resource ID is listed at https://cloud.google.com/kms/docs/getting-resource-ids#getting_the_id_for_a_key_and_version.
        """,
        type=str,
        hidden=True,
        default=None,
    )
