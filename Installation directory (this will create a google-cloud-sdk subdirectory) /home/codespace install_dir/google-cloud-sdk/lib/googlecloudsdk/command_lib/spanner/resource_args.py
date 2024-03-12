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
"""Shared resource flags for Cloud Spanner commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties

_PROJECT = properties.VALUES.core.project
_INSTANCE = properties.VALUES.spanner.instance

_CREATE_BACKUP_ENCRYPTION_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    '--encryption-type',
    apis.GetMessagesModule('spanner',
                           'v1').SpannerProjectsInstancesBackupsCreateRequest
    .EncryptionConfigEncryptionTypeValueValuesEnum,
    help_str='The encryption type of the backup.',
    required=False,
    custom_mappings={
        'USE_DATABASE_ENCRYPTION':
            ('use-database-encryption',
             'Use the same encryption configuration as the database.'),
        'GOOGLE_DEFAULT_ENCRYPTION':
            ('google-default-encryption', 'Use Google default encryption.'),
        'CUSTOMER_MANAGED_ENCRYPTION':
            ('customer-managed-encryption',
             'Use the provided Cloud KMS key for encryption. If this option is '
             'selected, kms-key must be set.')
    })

_COPY_BACKUP_ENCRYPTION_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    '--encryption-type',
    apis.GetMessagesModule(
        'spanner',
        'v1').CopyBackupEncryptionConfig.EncryptionTypeValueValuesEnum,
    help_str='The encryption type of the copied backup.',
    required=False,
    custom_mappings={
        'USE_CONFIG_DEFAULT_OR_BACKUP_ENCRYPTION': (
            'use-config-default-or-backup-encryption',
            ('Use the default encryption configuration if one exists. '
             'otherwise use the same encryption configuration as the source backup.'
            )),
        'GOOGLE_DEFAULT_ENCRYPTION':
            ('google-default-encryption', 'Use Google default encryption.'),
        'CUSTOMER_MANAGED_ENCRYPTION': (
            'customer-managed-encryption',
            ('Use the provided Cloud KMS key for encryption. If this option is '
             'selected, kms-key must be set.'))
    })

_RESTORE_DB_ENCRYPTION_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    '--encryption-type',
    apis.GetMessagesModule(
        'spanner',
        'v1').RestoreDatabaseEncryptionConfig.EncryptionTypeValueValuesEnum,
    help_str='The encryption type of the restored database.',
    required=False,
    custom_mappings={
        'USE_CONFIG_DEFAULT_OR_BACKUP_ENCRYPTION':
            ('use-config-default-or-backup-encryption',
             'Use the default encryption configuration if one exists, '
             'otherwise use the same encryption configuration as the backup.'),
        'GOOGLE_DEFAULT_ENCRYPTION':
            ('google-default-encryption', 'Use Google default encryption.'),
        'CUSTOMER_MANAGED_ENCRYPTION':
            ('customer-managed-encryption',
             'Use the provided Cloud KMS key for encryption. If this option is '
             'selected, kms-key must be set.')
    })

_INSTANCE_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    '--instance-type',
    apis.GetMessagesModule(
        'spanner',
        'v1').Instance.InstanceTypeValueValuesEnum,
    help_str='Specifies the type for this instance.',
    required=False,
    custom_mappings={
        'PROVISIONED': (
            'provisioned',
            ('Provisioned instances have dedicated resources, standard usage '
             'limits, and support.')),
        'FREE_INSTANCE': (
            'free-instance',
            ('Free trial instances provide no guarantees for dedicated '
             'resources, both node_count and processing_units should be 0. '
             'They come with stricter usage limits and limited support.')),
    })

_DEFAULT_STORAGE_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    '--default-storage-type',
    apis.GetMessagesModule('spanner',
                           'v1').Instance.DefaultStorageTypeValueValuesEnum,
    help_str='Specifies the default storage type for this instance.',
    required=False,
    hidden=True,
    custom_mappings={
        'SSD': ('ssd', ('Use ssd as default storage type for this instance')),
        'HDD': ('hdd', ('Use hdd as default storage type for this instance')),
    })

_EXPIRE_BEHAVIOR_MAPPER = arg_utils.ChoiceEnumMapper(
    '--expire-behavior',
    apis.GetMessagesModule(
        'spanner', 'v1').FreeInstanceMetadata.ExpireBehaviorValueValuesEnum,
    help_str='The expire behavior of a free trial instance.',
    required=False,
    custom_mappings={
        'FREE_TO_PROVISIONED':
            ('free-to-provisioned',
             ('When the free trial instance expires, upgrade the instance to a '
              'provisioned instance.')),
        'REMOVE_AFTER_GRACE_PERIOD':
            ('remove-after-grace-period',
             ('When the free trial instance expires, disable the instance, '
              'and delete it after the grace period passes if it has not been '
              'upgraded to a provisioned instance.')),
    })


def InstanceAttributeConfig():
  """Get instance resource attribute with default value."""
  return concepts.ResourceParameterAttributeConfig(
      name='instance',
      help_text='The Cloud Spanner instance for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(_INSTANCE)])


def DatabaseAttributeConfig():
  """Get database resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='database',
      help_text='The Cloud Spanner database for the {resource}.')


def BackupAttributeConfig():
  """Get backup resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='backup',
      help_text='The Cloud Spanner backup for the {resource}.')


def SessionAttributeConfig():
  """Get session resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='session', help_text='The Cloud Spanner session for the {resource}.')


def KmsKeyAttributeConfig():
  # For anchor attribute, help text is generated automatically.
  return concepts.ResourceParameterAttributeConfig(name='kms-key')


def KmsKeyringAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-keyring', help_text='KMS keyring id of the {resource}.')


def KmsLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-location', help_text='Cloud location for the {resource}.')


def KmsProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-project', help_text='Cloud project id for the {resource}.')


def GetInstanceResourceSpec():
  return concepts.ResourceSpec(
      'spanner.projects.instances',
      resource_name='instance',
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetDatabaseResourceSpec():
  return concepts.ResourceSpec(
      'spanner.projects.instances.databases',
      resource_name='database',
      databasesId=DatabaseAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetKmsKeyResourceSpec():
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name='key',
      cryptoKeysId=KmsKeyAttributeConfig(),
      keyRingsId=KmsKeyringAttributeConfig(),
      locationsId=KmsLocationAttributeConfig(),
      projectsId=KmsProjectAttributeConfig())


def GetBackupResourceSpec():
  return concepts.ResourceSpec(
      'spanner.projects.instances.backups',
      resource_name='backup',
      backupsId=BackupAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetSessionResourceSpec():
  return concepts.ResourceSpec(
      'spanner.projects.instances.databases.sessions',
      resource_name='session',
      sessionsId=SessionAttributeConfig(),
      databasesId=DatabaseAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddInstanceResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Cloud Spanner instance.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the instance ID is a positional rather
      than a flag.
  """
  name = 'instance' if positional else '--instance'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetInstanceResourceSpec(),
      'The Cloud Spanner instance {}.'.format(verb),
      required=True).AddToParser(parser)


def AddDatabaseResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Cloud Spanner database.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the database ID is a positional rather
      than a flag.
  """
  name = 'database' if positional else '--database'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetDatabaseResourceSpec(),
      'The Cloud Spanner database {}.'.format(verb),
      required=True).AddToParser(parser)


def AddKmsKeyResourceArg(parser, verb, positional=False):
  """Add a resource argument for a KMS Key used to create a CMEK database.

  Args:
    parser: argparser, the parser for the command.
    verb: str, the verb used to describe the resource, such as 'to create'.
    positional: bool, optional. True if the resource arg is postional rather
      than a flag.
  """
  kms_key_name = 'kms-key' if positional else '--kms-key'
  kms_key_names = 'kms-keys' if positional else '--kms-keys'
  group = parser.add_group('KMS key name group', mutex=True)
  concept_parsers.ConceptParser([
      presentation_specs.ResourcePresentationSpec(
          kms_key_name,
          GetKmsKeyResourceSpec(),
          'Cloud KMS key to be used {}.'.format(verb),
          required=False,
          group=group,
      ),
      presentation_specs.ResourcePresentationSpec(
          kms_key_names,
          GetKmsKeyResourceSpec(),
          'Cloud KMS key(s) to be used {}.'.format(verb),
          required=False,
          prefixes=True,
          hidden=True,
          plural=True,
          group=group,
          flag_name_overrides={
              'kms-location': '',
              'kms-keyring': '',
              'kms-project': '',
          },
      ),
  ]).AddToParser(parser)


def AddSessionResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Cloud Spanner session.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the session ID is a positional rather
      than a flag.
  """
  name = 'session' if positional else '--session'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetSessionResourceSpec(),
      'The Cloud Spanner session {}.'.format(verb),
      required=True).AddToParser(parser)


def AddBackupResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Cloud Spanner backup.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the backup ID is a positional rather
      than a flag.
  """
  name = 'backup' if positional else '--backup'

  concept_parsers.ConceptParser.ForResource(
      name,
      GetBackupResourceSpec(),
      'The Cloud Spanner backup {}.'.format(verb),
      required=True).AddToParser(parser)


def AddCreateBackupEncryptionTypeArg(parser):
  return _CREATE_BACKUP_ENCRYPTION_TYPE_MAPPER.choice_arg.AddToParser(parser)


def GetCreateBackupEncryptionType(args):
  return _CREATE_BACKUP_ENCRYPTION_TYPE_MAPPER.GetEnumForChoice(
      args.encryption_type)


def AddCopyBackupResourceArgs(parser):
  """Add backup resource args (source, destination) for copy command."""
  arg_specs = [
      presentation_specs.ResourcePresentationSpec(
          '--source',
          GetBackupResourceSpec(),
          'TEXT',
          required=True,
          flag_name_overrides={
              'instance': '--source-instance',
              'backup': '--source-backup'
          }),
      presentation_specs.ResourcePresentationSpec(
          '--destination',
          GetBackupResourceSpec(),
          'TEXT',
          required=True,
          flag_name_overrides={
              'instance': '--destination-instance',
              'backup': '--destination-backup',
          }),
  ]

  concept_parsers.ConceptParser(arg_specs).AddToParser(parser)


def AddCopyBackupEncryptionTypeArg(parser):
  return _COPY_BACKUP_ENCRYPTION_TYPE_MAPPER.choice_arg.AddToParser(parser)


def GetCopyBackupEncryptionType(args):
  return _COPY_BACKUP_ENCRYPTION_TYPE_MAPPER.GetEnumForChoice(
      args.encryption_type)


def AddRestoreResourceArgs(parser):
  """Add backup resource args (source, destination) for restore command."""
  arg_specs = [
      presentation_specs.ResourcePresentationSpec(
          '--source',
          GetBackupResourceSpec(),
          'TEXT',
          required=True,
          flag_name_overrides={
              'instance': '--source-instance',
              'backup': '--source-backup'
          }),
      presentation_specs.ResourcePresentationSpec(
          '--destination',
          GetDatabaseResourceSpec(),
          'TEXT',
          required=True,
          flag_name_overrides={
              'instance': '--destination-instance',
              'database': '--destination-database',
          }),
  ]

  concept_parsers.ConceptParser(arg_specs).AddToParser(parser)


def AddRestoreDbEncryptionTypeArg(parser):
  return _RESTORE_DB_ENCRYPTION_TYPE_MAPPER.choice_arg.AddToParser(parser)


def GetRestoreDbEncryptionType(args):
  return _RESTORE_DB_ENCRYPTION_TYPE_MAPPER.GetEnumForChoice(
      args.encryption_type)


def GetAndValidateKmsKeyName(args):
  """Parse the KMS key resource arg, make sure the key format is correct.

  Returns:
    str: when --kms-key is used.
    list: when --kms-keys is used.

  TODO(b/247020647): Rename this function to GetAndValidateKmsKeyNameOrNames.
  """
  kms_key_name = args.CONCEPTS.kms_key.Parse()
  kms_key_names = args.CONCEPTS.kms_keys.Parse()
  if kms_key_name:
    return kms_key_name.RelativeName()
  elif kms_key_names:
    return [kms_key_name.RelativeName() for kms_key_name in kms_key_names]
  else:
    # If parsing failed but args were specified, raise error
    for keyword in [
        'kms-key',
        'kms-keyring',
        'kms-location',
        'kms-project',
        'kms-keys',
    ]:
      if getattr(args, keyword.replace('-', '_'), None):
        raise exceptions.InvalidArgumentException(
            '--kms-project --kms-location --kms-keyring --kms-key or'
            ' --kms-keys',
            'For a single KMS key, specify fully qualified KMS key ID with'
            ' --kms-key, or use combination of --kms-project, --kms-location,'
            ' --kms-keyring and '
            + '--kms-key to specify the key ID in pieces. Or specify fully'
            ' qualified KMS key ID with --kms-keys.',
        )
    return None  # User didn't specify KMS key


def AddInstanceTypeArg(parser):
  return _INSTANCE_TYPE_MAPPER.choice_arg.AddToParser(parser)


def GetInstanceType(args):
  return _INSTANCE_TYPE_MAPPER.GetEnumForChoice(args.instance_type)


def AddDefaultStorageTypeArg(parser):
  return _DEFAULT_STORAGE_TYPE_MAPPER.choice_arg.AddToParser(parser)


def GetDefaultStorageTypeArg(args):
  return _DEFAULT_STORAGE_TYPE_MAPPER.GetEnumForChoice(
      args.default_storage_type)


def AddExpireBehaviorArg(parser):
  return _EXPIRE_BEHAVIOR_MAPPER.choice_arg.AddToParser(parser)


def GetExpireBehavior(args):
  return _EXPIRE_BEHAVIOR_MAPPER.GetEnumForChoice(args.expire_behavior)
