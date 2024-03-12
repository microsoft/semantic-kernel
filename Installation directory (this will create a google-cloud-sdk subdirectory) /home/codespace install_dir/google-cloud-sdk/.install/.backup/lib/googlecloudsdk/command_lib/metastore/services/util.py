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
"""Utilities for "gcloud metastore services" commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import xml.etree.cElementTree as element_tree

from googlecloudsdk.command_lib.metastore import parsers
from googlecloudsdk.core import properties


def GetTier():
  """Returns the value of the metastore/tier config property.

  Config properties can be overridden with command line flags. If the --tier
  flag was provided, this will return the value provided with the flag.
  """
  return properties.VALUES.metastore.tier.Get(required=True)


def LoadHiveMetatsoreConfigsFromXmlFile(file_arg):
  """Convert Input XML file into Hive metastore configurations."""
  hive_metastore_configs = {}
  root = element_tree.fromstring(file_arg)

  for prop in root.iter('property'):
    hive_metastore_configs[prop.find('name').text] = prop.find('value').text
  return hive_metastore_configs


def GenerateNetworkConfigFromSubnetList(unused_ref, args, req):
  """Generates the NetworkConfig message from the list of subnetworks.

  Args:
    args: The request arguments.
    req: A request with `service` field.

  Returns:
    A request with network configuration field if `consumer-subnetworks` is
    present in the arguments.
  """
  if args.consumer_subnetworks:
    req.service.networkConfig = {
        'consumers': [
            {'subnetwork': parsers.ParseSubnetwork(s, args.location)}
            for s in args.consumer_subnetworks
        ]
    }
  return req


def GenerateAuxiliaryVersionsConfigFromList(unused_ref, args, req):
  """Generates the auxiliary versions map from the list of auxiliary versions.

  Args:
    args: The request arguments.
    req: A request with `service` field.

  Returns:
    If `auxiliary-versions` is present in the arguments, a request with hive
    metastore config's auxiliary versions map field is returned.
    Otherwise the original request is returned.
  """
  if args.auxiliary_versions:
    if req.service.hiveMetastoreConfig is None:
      req.service.hiveMetastoreConfig = {}
    req.service.hiveMetastoreConfig.auxiliaryVersions = (
        _GenerateAuxiliaryVersionsVersionList(args.auxiliary_versions)
    )
  return req


def LoadAuxiliaryVersionsConfigsFromYamlFile(file_contents):
  """Convert Input YAML file into auxiliary versions configurations map.

  Args:
    file_contents: The YAML file contents of the file containing the auxiliary
      versions configurations.

  Returns:
    The auxiliary versions configuration mapping with service name as the key
    and config as the value.
  """
  aux_versions = {}
  for aux_config in file_contents:
    aux_versions[aux_config['name']] = {'version': aux_config['version']}
    if 'config_overrides' in aux_config:
      aux_versions[aux_config['name']]['configOverrides'] = aux_config[
          'config_overrides'
      ]
  return aux_versions


def LoadScheduledBackupConfigsFromJsonFile(file_contents):
  """Convert Input JSON file into scheduled backup configurations map.

  Args:
    file_contents: The JSON file contents of the file containing the scheduled
      backup configurations.

  Returns:
    The scheduled backup configuration mapping with key and value.
  """
  try:
    scheduled_backup_configs = json.loads(file_contents)

    config = {}

    if 'enabled' in scheduled_backup_configs:
      config['enabled'] = scheduled_backup_configs.pop('enabled')

    if config.get('enabled', False):
      if 'cron_schedule' not in scheduled_backup_configs:
        raise ValueError('Missing required field: cron_schedule')
      if 'backup_location' not in scheduled_backup_configs:
        raise ValueError('Missing required field: backup_location')

    config['cron_schedule'] = scheduled_backup_configs.get('cron_schedule')
    config['backup_location'] = scheduled_backup_configs.get('backup_location')
    config['time_zone'] = scheduled_backup_configs.get('time_zone', 'UTC')

    return config

  except (json.JSONDecodeError, KeyError) as e:
    raise ValueError(f'Invalid scheduled backup configuration JSON data: {e}')


def _GenerateAdditionalProperties(values_dict):
  """Format values_dict into additionalProperties-style dict."""
  props = [{'key': k, 'value': v} for k, v in sorted(values_dict.items())]
  return {'additionalProperties': props}


def _GenerateUpdateMask(args):
  """Constructs updateMask for patch requests.

  Args:
    args: The parsed args namespace from CLI.

  Returns:
    String containing update mask for patch request.
  """
  hive_metastore_configs = 'hive_metastore_config.config_overrides'
  labels = 'labels'
  arg_name_to_field = {
      '--port': 'port',
      '--tier': 'tier',
      '--instance-size': 'scaling_config.instance_size',
      '--scaling-factor': 'scaling_config.scaling_factor',
      '--update-hive-metastore-configs-from-file': (
          'hive_metastore_config.config_overrides'
      ),
      '--clear-hive-metastore-configs': hive_metastore_configs,
      '--clear-labels': labels,
      '--kerberos-principal': 'hive_metastore_config.kerberos_config.principal',
      '--keytab': 'hive_metastore_config.kerberos_config.keytab',
      '--krb5-config': (
          'hive_metastore_config.kerberos_config.krb5_config_gcs_uri'
      ),
      '--maintenance-window-day': 'maintenance_window',
      '--maintenance-window-hour': 'maintenance_window',
      '--data-catalog-sync': 'metadataIntegration.dataCatalogConfig.enabled',
      '--no-data-catalog-sync': 'metadataIntegration.dataCatalogConfig.enabled',
      '--endpoint-protocol': 'hive_metastore_config.endpoint_protocol',
      '--add-auxiliary-versions': 'hive_metastore_config.auxiliary_versions',
      '--update-auxiliary-versions-from-file': (
          'hive_metastore_config.auxiliary_versions'
      ),
      '--clear-auxiliary-versions': 'hive_metastore_config.auxiliary_versions',
      '--scheduled-backup-configs-from-file': 'scheduled_backup',
      '--enable-scheduled-backup': 'scheduled_backup',
      '--no-enable-scheduled-backup': 'scheduled_backup.enabled',
      '--scheduled-backup-cron': 'scheduled_backup',
      '--scheduled-backup-location': 'scheduled_backup',
  }

  update_mask = set()
  for arg_name in set(args.GetSpecifiedArgNames()).intersection(
      arg_name_to_field
  ):
    update_mask.add(arg_name_to_field[arg_name])
  hive_metastore_configs_update_mask_prefix = hive_metastore_configs + '.'
  if hive_metastore_configs not in update_mask:
    if args.update_hive_metastore_configs:
      for key in args.update_hive_metastore_configs:
        update_mask.add(hive_metastore_configs_update_mask_prefix + key)
    if args.remove_hive_metastore_configs:
      for key in args.remove_hive_metastore_configs:
        update_mask.add(hive_metastore_configs_update_mask_prefix + key)
  labels_update_mask_prefix = labels + '.'
  if labels not in update_mask:
    if args.update_labels:
      for key in args.update_labels:
        update_mask.add(labels_update_mask_prefix + key)
    if args.remove_labels:
      for key in args.remove_labels:
        update_mask.add(labels_update_mask_prefix + key)
  return ','.join(sorted(update_mask))


def SetServiceRequestUpdateHiveMetastoreConfigs(
    unused_job_ref, args, update_service_req
):
  """Modify the Service update request to update, remove, or clear Hive metastore configurations.

  Args:
    unused_ref: A resource ref to the parsed Service resource.
    args: The parsed args namespace from CLI.
    update_service_req: Created Update request for the API call.

  Returns:
    Modified request for the API call.
  """
  hive_metastore_configs = {}
  if args.update_hive_metastore_configs:
    hive_metastore_configs = args.update_hive_metastore_configs
  if args.update_hive_metastore_configs_from_file:
    hive_metastore_configs = LoadHiveMetatsoreConfigsFromXmlFile(
        args.update_hive_metastore_configs_from_file
    )
  update_service_req.service.hiveMetastoreConfig.configOverrides = (
      _GenerateAdditionalProperties(hive_metastore_configs)
  )
  return update_service_req


def GenerateUpdateAuxiliaryVersionsConfigs(
    unused_job_ref, args, update_service_req
):
  """Modify the Service update request to add or clear list of auxiliary versions configurations.

  Args:
    unused_ref: A resource ref to the parsed Service resource.
    args: The parsed args namespace from CLI.
    update_service_req: Created Update request for the API call.

  Returns:
    Modified request for the API call containing auxiliary version updates if
    specified else the original request.
  """
  if update_service_req.service.hiveMetastoreConfig is None:
    update_service_req.service.hiveMetastoreConfig = {}
  if args.clear_auxiliary_versions:
    update_service_req.service.hiveMetastoreConfig.auxiliaryVersions = {}
  if args.add_auxiliary_versions:
    update_service_req.service.hiveMetastoreConfig.auxiliaryVersions = (
        _GenerateAuxiliaryVersionsVersionList(args.add_auxiliary_versions)
    )
  return update_service_req


def _GenerateAuxiliaryVersionsVersionList(aux_versions):
  return _GenerateAdditionalProperties({
      'aux-' + version.replace('.', '-'): {'version': version}
      for version in aux_versions
  })


def UpdateServiceMaskHook(unused_ref, args, update_service_req):
  """Constructs updateMask for update requests of Dataproc Metastore services.

  Args:
    unused_ref: A resource ref to the parsed Service resource.
    args: The parsed args namespace from CLI.
    update_service_req: Created Update request for the API call.

  Returns:
    Modified request for the API call.
  """
  update_service_req.updateMask = _GenerateUpdateMask(args)
  return update_service_req
