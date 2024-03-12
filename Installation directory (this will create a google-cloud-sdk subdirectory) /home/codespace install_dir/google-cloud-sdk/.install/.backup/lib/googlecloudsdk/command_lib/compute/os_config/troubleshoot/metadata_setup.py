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
"""Utility function for OS Config Troubleshooter to check metadata setup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.os_config.troubleshoot import utils

# These represent possible true values for metadata fields. These are found at
# https://cloud.google.com/compute/docs/metadata/setting-custom-metadata#boolean
_METADATA_BOOL = [
    'true',
    'y',
    'yes',
    '1',
    1
]
_ENABLE_OSCONFIG = 'enable-osconfig'
_DISABLED_FEATURES = 'osconfig-disabled-features'


def _DisabledMessage(instance, release_track):
  command_args = ['compute', 'project_info', 'add-metadata',
                  '--metadata=enable-osconfig=true']
  project_command = utils.GetCommandString(command_args, release_track)
  instance_args = ['compute', 'instances', 'add-metadata', instance.name,
                   '--metadata=enable-osconfig=true']
  instance_command = utils.GetCommandString(instance_args, release_track)
  return ('No\n'
          'OS Config agent is not enabled for this VM instance. To enable for'
          ' all VMs in this project, run:\n\n' + project_command + '\n\n'
          'To enable for this VM, run:\n\n' + instance_command)


def _EnabledWithDisabledFeaturesMessage(disabled_features):
  return (
      'Yes\n'
      'OS Config agent is enabled for this VM instance, but the following '
      'features are disabled:\n[' + disabled_features + '].\nSee '
      'https://cloud.google.com/compute/docs/manage-os#disable-features'
      ' for instructions on how to make changes to this setting.'
      )


def _GetMetadataValue(metadata, key):
  """Gets the value of the key field of the given metadata list.

  Args:
    metadata: The metadata to look through.
    key: the key to look for

  Returns:
  The value of the key, None if the metadata field does not exist.
  """
  return next((md.value for md in metadata if md.key == key), None)


def Check(project, instance, release_track, exception=None):
  """Checks if the metadata is set up correctly."""
  response_message = '> Is the OS Config agent enabled? '

  continue_flag = False
  enable_osconfig = None
  disabled_features = None

  if exception:
    response_message += utils.UnknownMessage(exception)
    return utils.Response(continue_flag, response_message)

  # Check the instance metadata.
  instance_metadata = instance.metadata.items
  if instance_metadata:
    enable_osconfig = _GetMetadataValue(instance_metadata, _ENABLE_OSCONFIG)
    disabled_features = _GetMetadataValue(instance_metadata, _DISABLED_FEATURES)

  # Get any missing metadata from the project.
  project_metadata = project.commonInstanceMetadata.items
  if project_metadata:
    if not enable_osconfig:
      enable_osconfig = _GetMetadataValue(project_metadata, _ENABLE_OSCONFIG)
    if not disabled_features:
      disabled_features = _GetMetadataValue(project_metadata,
                                            _DISABLED_FEATURES)

  if enable_osconfig:
    if enable_osconfig.lower() in _METADATA_BOOL:
      continue_flag = True
      if disabled_features:
        response_message += _EnabledWithDisabledFeaturesMessage(
            disabled_features)
      else:
        response_message += 'Yes'
    else:
      response_message += _DisabledMessage(instance, release_track)
  else:
    response_message += _DisabledMessage(instance, release_track)

  return utils.Response(continue_flag, response_message)
