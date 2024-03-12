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
"""Utility function for OS Config Troubleshooter to check network config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.os_config.troubleshoot import utils
from googlecloudsdk.core import exceptions


def _GetSubnetwork(client, subnetwork_uri):
  """Gets the subnetwork object."""
  uri = subnetwork_uri.split('/')

  project = _GetValueFromUri(uri, 'projects')
  region = _GetValueFromUri(uri, 'regions')
  name = _GetValueFromUri(uri, 'subnetworks')
  request = client.messages.ComputeSubnetworksGetRequest(
      project=project,
      region=region,
      subnetwork=name
  )
  return client.MakeRequests([(client.apitools_client.subnetworks,
                               'Get', request)])[0]


def _GetValueFromUri(uri, field):
  """Gets the value of the desired field from the provided uri.

  The uri should be an array containing the field keys directly followed by
  their values. An example array is [projects, example-project], where
  `projects` is the field and `example-project` is its value.

  Args:
    uri: the uri from which to get fields, in array form.
    field: the desired field to Get

  Returns:
    The value of the field in the uri, None if the field doesn't exist.
  """
  index = uri.index(field)
  if index == -1:
    return None
  return uri[index + 1]


def Check(client, instance):
  """Checks if the network configuration is set correctly."""
  continue_flag = False
  response_message = ('> Does this instance have a public IP or Private Google '
                      'Access? ')

  # A network interface must exist for the instance.
  # https://cloud.google.com/vpc/docs/create-use-multiple-interfaces#specifications
  network_interface = instance.networkInterfaces[0]
  if not network_interface.accessConfigs:
    response_message += (
        'No\n'
        'No access config has been specified for this instance. This means '
        'the VM instance has no external internet access. Visit '
        'https://cloud.google.com/sdk/gcloud/reference/compute/instances/add-access-config'
        ' for instructions on how to add an access config to your instance.'
    )
    return utils.Response(continue_flag, response_message)

  access_config = network_interface.accessConfigs[0]
  has_private_google_access = False
  config = access_config.natIP
  if not config:
    subnetwork = None
    try:
      subnetwork = _GetSubnetwork(client, network_interface.subnetwork)
    except exceptions.Error as e:
      response_message += utils.UnknownMessage(e)
      return utils.Response(continue_flag, response_message)

    if not subnetwork.privateIpGoogleAccess:
      response_message += (
          'No\n'
          'This instance does not have a public IP address, and it does not'
          ' have Private Google Access. Visit '
          'https://cloud.google.com/compute/docs/ip-addresses#externaladdresses'
          ' for instructions on how to assign an external IP address to an '
          'instance, and '
          'https://cloud.google.com/vpc/docs/configure-private-google-access#enabling-pga'
          ' on how to configure Private Google Access for a VPC network.'
      )
      return utils.Response(continue_flag, response_message)
    has_private_google_access = True

  continue_flag = True
  response_message += 'Yes\nThis instance has ' + ('Private Google Access.'
                                                   if has_private_google_access
                                                   else 'a public IP.')
  return utils.Response(continue_flag, response_message)
