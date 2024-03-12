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
"""Flags and helpers for general Cloud NetApp Files commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.netapp import constants

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties

## Attribute configs ##


def GetLocationAttributeConfig():
  """Return the Location Attribute Config for resources.

  Returns:
    ResourceParameterAttributeConfig for location.
  """
  fallthroughs = [
      ## if location is not set, use value from
      ## gcloud config get-value netapp/location or netapp/region
      deps.ArgFallthrough('--location'),
      deps.PropertyFallthrough(properties.VALUES.netapp.location),
  ]

  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=fallthroughs,
      help_text='The location of the {resource}.')


def GetStoragePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'storage_pool', 'The instance of the {resource}.')


def GetVolumeAttributeConfig(positional=True):
  """Return the Volume Attribute Config for resources.

  Args:
    positional: boolean value describing whether volume attribute is conditional

  Returns:
    volume resource parameter attribute config for resource specs

  """
  if positional:
    fallthroughs = []
  else:
    ## For when we need a volume attribute in Snapshot resource spec, we want
    ## to assign fallthrough flags
    fallthroughs = [deps.ArgFallthrough('--volume')]
  help_text = ('The instance of the {resource}' if positional else (
      'The volume of the {resource}'))
  return concepts.ResourceParameterAttributeConfig(
      name='volume', fallthroughs=fallthroughs, help_text=help_text)


def GetSnapshotAttributeConfig(positional=True):
  if positional:
    help_text = 'The instance of the {resource}'
  else:
    help_text = 'The snapshot of the {resource}'
  return concepts.ResourceParameterAttributeConfig(
      'snapshot', help_text=help_text)


def GetReplicationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'replication', 'The instance of the {resource}')


def GetOperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'operation', 'The Cloud NetApp operation.')


def GetActiveDirectoryAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'active_directory', 'The instance of the {resource}.'
  )


def GetBackupVaultAttributeConfig(positional=True):
  fallthroughs = []
  if not positional:
    ## For when we need a Backup Vault attribute in Backup resource spec
    ## we want to assign fallthrough flags
    fallthroughs = [deps.ArgFallthrough('--backup-vault')]
  return concepts.ResourceParameterAttributeConfig(
      'backup_vault', 'The Backup Vault of the {resource}.',
      fallthroughs=fallthroughs
  )


def GetBackupAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'backup', 'The instance of the {resource}.')


def GetBackupPolicyAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'backup_policy', 'The instance of the {resource}.'
  )


def GetKmsConfigAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'kms_config', 'The instance of the {resource}')


def GetKeyRingAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'key_ring', 'The instance of the {resource}.'
  )


def GetCryptoKeyAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'crypto_key', 'The instance of the {resource}.'
  )


## Resource Specs ##


def GetLocationResourceSpec():
  location_attribute_config = GetLocationAttributeConfig()
  location_attribute_config.fallthroughs = []
  return concepts.ResourceSpec(
      constants.LOCATIONS_COLLECTION,
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config)


def GetListingLocationResourceSpec():
  location_attribute_config = GetLocationAttributeConfig()
  location_attribute_config.fallthroughs.insert(
      0, deps.Fallthrough(lambda: '-', hint='uses all locations by default.'))
  return concepts.ResourceSpec(
      constants.LOCATIONS_COLLECTION,
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config)


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      constants.OPERATIONS_COLLECTION,
      resource_name='operation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      operationsId=GetOperationAttributeConfig())


def GetStoragePoolResourceSpec():
  return concepts.ResourceSpec(
      constants.STORAGEPOOLS_COLLECTION,
      resource_name='storage_pool',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      storagePoolsId=GetStoragePoolAttributeConfig())


def GetVolumeResourceSpec(positional=True):
  return concepts.ResourceSpec(
      constants.VOLUMES_COLLECTION,
      resource_name='volume',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      volumesId=GetVolumeAttributeConfig(positional=positional),
  )


def GetSnapshotResourceSpec(source_snapshot_op=False, positional=True):
  """Gets the Resource Spec for Snapshot.

  Args:
    source_snapshot_op: Boolean on whether operation uses snapshot as source or
      not.
    positional: Boolean on whether resource is positional arg ornot

  Returns:
    The Resource Spec for Snapshot
  """
  location_attribute_config = GetLocationAttributeConfig()
  volume_attribute_config = GetVolumeAttributeConfig(positional=False)
  if source_snapshot_op:
    # if revert op or backup op (create, update) that is a source snapshot op,
    # we don't want volume attribute to have any fallthroughs
    # (--volume arg) since volume is positional in revert.
    volume_attribute_config.fallthroughs = []
  if not positional:
    location_attribute_config.fallthroughs = [
        deps.PropertyFallthrough(properties.VALUES.netapp.location),
    ]
  return concepts.ResourceSpec(
      constants.SNAPSHOTS_COLLECTION,
      resource_name='snapshot',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config,
      volumesId=volume_attribute_config,
      snapshotsId=GetSnapshotAttributeConfig(positional=positional))


def GetReplicationResourceSpec():
  location_attribute_config = GetLocationAttributeConfig()
  volume_attribute_config = GetVolumeAttributeConfig(positional=False)
  return concepts.ResourceSpec(
      constants.REPLICATIONS_COLLECTION,
      resource_name='replication',
      api_version=constants.BETA_API_VERSION,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config,
      volumesId=volume_attribute_config,
      replicationsId=GetReplicationAttributeConfig())


def GetActiveDirectoryResourceSpec():
  return concepts.ResourceSpec(
      constants.ACTIVEDIRECTORIES_COLLECTION,
      resource_name='active_directory',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      activeDirectoriesId=GetActiveDirectoryAttributeConfig())


def GetKmsConfigResourceSpec():
  return concepts.ResourceSpec(
      constants.KMSCONFIGS_COLLECTION,
      resource_name='kms_config',
      api_version=constants.BETA_API_VERSION,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      kmsConfigsId=GetKmsConfigAttributeConfig())


def GetBackupVaultResourceSpec(positional=True):
  return concepts.ResourceSpec(
      constants.BACKUPVAULTS_COLLECTION,
      resource_name='backup_vault',
      api_version=constants.BETA_API_VERSION,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      backupVaultsId=GetBackupVaultAttributeConfig(positional=positional),
  )


def GetBackupResourceSpec(positional=True):
  location_attribute_config = GetLocationAttributeConfig()
  backup_vault_attribute_config = GetBackupVaultAttributeConfig(
      positional=False
  )
  if not positional:
    location_attribute_config.fallthroughs = [
        deps.PropertyFallthrough(properties.VALUES.netapp.location),
    ]
  return concepts.ResourceSpec(
      constants.BACKUPS_COLLECTION,
      resource_name='backup',
      api_version=constants.BETA_API_VERSION,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config,
      backupVaultsId=backup_vault_attribute_config,
      backupsId=GetBackupAttributeConfig(),
  )


def GetBackupPolicyResourceSpec():
  return concepts.ResourceSpec(
      constants.BACKUPPOLICIES_COLLECTION,
      resource_name='backup_policy',
      api_version=constants.BETA_API_VERSION,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      backupPoliciesId=GetBackupPolicyAttributeConfig())


def GetCryptoKeyResourceSpec():
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name='crypto_key',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetLocationAttributeConfig(),
      keyRingsId=GetKeyRingAttributeConfig(),
      cryptoKeysId=GetCryptoKeyAttributeConfig()
  )

## Presentation Specs ##


def GetLocationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'location', GetLocationResourceSpec(), group_help, required=True)


def GetResourceListingLocationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      '--location',
      GetListingLocationResourceSpec(),
      group_help)


def GetOperationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'operation', GetOperationResourceSpec(), group_help, required=True)


def GetStoragePoolPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'storage_pool', GetStoragePoolResourceSpec(), group_help, required=True)


def GetVolumePresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'volume', GetVolumeResourceSpec(), group_help, required=True)


def GetSnapshotPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'snapshot',
      GetSnapshotResourceSpec(),
      group_help,
      required=True,
      flag_name_overrides={'volume': ''})


def GetReplicationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'replication',
      GetReplicationResourceSpec(),
      group_help,
      required=True,
      flag_name_overrides={'volume': ''})


def GetActiveDirectoryPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'active_directory',
      GetActiveDirectoryResourceSpec(),
      group_help,
      required=True)


def GetKmsConfigPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'kms_config',
      GetKmsConfigResourceSpec(),
      group_help,
      required=True)


def GetBackupVaultPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'backup_vault',
      GetBackupVaultResourceSpec(),
      group_help,
      required=True)


def GetBackupPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'backup',
      GetBackupResourceSpec(),
      group_help,
      required=True,
      flag_name_overrides={'backup_vault': ''})


# TODO(b/290375665): Add more unit tests to test Backup Poicy
# Presentation, resource specs and flags
def GetBackupPolicyPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'backup_policy',
      GetBackupPolicyResourceSpec(),
      group_help,
      required=True)

## Add args to arg parser ##


def AddResourceDescriptionArg(parser, resource_name):
  """Add Description arg to arg_parser for a resource called resource_name."""
  parser.add_argument(
      '--description',
      required=False,
      help='A description of the Cloud NetApp {}'.format(resource_name))


def AddResourceCapacityArg(parser, resource_name, required=True):
  """Add Capacity arg to arg_parser for a resource called resource_name."""
  parser.add_argument(
      '--capacity',
      type=arg_parsers.BinarySize(
          default_unit='GiB', suggested_binary_size_scales=['GiB', 'TiB']),
      required=required,
      help=('The desired capacity of the {} in GiB or TiB units.'
            'If no capacity unit is specified, GiB is assumed.'.format(
                resource_name)))


def AddResourceAsyncFlag(parser):
  help_text = """Return immediately, without waiting for the operation
  in progress to complete."""
  concepts.ResourceParameterAttributeConfig(name='async', help_text=help_text)
  base.ASYNC_FLAG.AddToParser(parser)
