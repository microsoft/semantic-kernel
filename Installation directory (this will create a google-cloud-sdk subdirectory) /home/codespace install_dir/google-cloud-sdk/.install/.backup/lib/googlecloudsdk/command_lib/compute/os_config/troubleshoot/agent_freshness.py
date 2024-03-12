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
"""Utility function for OS Config Troubleshooter to check agent freshness."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import utils

_API_CLIENT_NAME = 'osconfig'
_UNKNOWN_MESSAGE = (
    'Unknown\n'
    'The version of OS Config agent running on this instance is unknown. '
    'Visit https://cloud.google.com/compute/docs/manage-os#check-install '
    'on how to check if the agent is installed and running.')


def _GetReleaseTrack(release_track):
  return 'v1alpha' if release_track == base.ReleaseTrack.ALPHA else 'v1'


def Check(project, instance, zone, release_track):
  """Checks whether the OS Config agent is up to date."""
  continue_flag = False
  response_message = '> Is the OS Config agent up to date? '

  client = apis.GetClientInstance(_API_CLIENT_NAME,
                                  _GetReleaseTrack(release_track))
  inventory_service = client.projects_locations_instances_inventories

  name = 'projects/{}/locations/{}/instances/{}/inventory'.format(
      project.name, zone, instance.name)
  inventory = None
  try:
    inventory = inventory_service.Get(
        client.MESSAGES_MODULE
        .OsconfigProjectsLocationsInstancesInventoriesGetRequest(
            name=name,
            view=client.MESSAGES_MODULE
            .OsconfigProjectsLocationsInstancesInventoriesGetRequest
            .ViewValueValuesEnum.FULL))
  except exceptions.HttpNotFoundError:
    response_message += _UNKNOWN_MESSAGE
    return utils.Response(continue_flag, response_message)
  except exceptions.HttpForbiddenError as e:
    response_message += utils.UnknownMessage(e)
    return utils.Response(continue_flag, response_message)

  if not inventory.items.additionalProperties:
    response_message += _UNKNOWN_MESSAGE
    return utils.Response(continue_flag, response_message)

  # Check if the OS Config Agent is installed.
  installed_flag = False
  for item in inventory.items.additionalProperties:
    key = item.key
    if key.startswith(
        'installedPackage') and key.find('google-osconfig-agent') != -1:
      installed_flag = True
      break

  if not installed_flag:
    response_message += (
        'No\n'
        'The OS Config agent is not installed on this VM. See '
        'https://cloud.google.com/compute/docs/manage-os#agent-install '
        'on how to install the agent.'
        )
    return utils.Response(continue_flag, response_message)

  # Check if the agent has an available update.
  for item in inventory.items.additionalProperties:
    key = item.key
    if key.startswith(
        'availablePackage') and key.find('google-osconfig-agent') != -1:
      response_message += (
          'No\n'
          'The version of OS Config agent running on this VM '
          'instance is not the latest version. See '
          'https://cloud.google.com/compute/docs/manage-os/upgrade-vm-manager#update-agent'
          ' on how to update the agent.'
          )
      return utils.Response(continue_flag, response_message)

  continue_flag = True
  response_message += 'Yes'
  return utils.Response(continue_flag, response_message)
