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

"""A shared library to support implementation of Firebase Test Lab commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

OUTCOMES_FORMAT = """
          table[box](
            outcome.color(red=Fail, green=Pass, blue=Flaky, yellow=Inconclusive),
            axis_value:label=TEST_AXIS_VALUE,
            test_details:label=TEST_DETAILS
          )
"""


def GetError(error):
  """Returns a ready-to-print string representation from the http response.

  Args:
    error: the Http error response, whose content is a JSON-format string for
      most cases (e.g. invalid test dimension), but can be just a string other
      times (e.g. invalid URI for CLOUDSDK_TEST_ENDPOINT).

  Returns:
    A ready-to-print string representation of the error.
  """
  try:
    data = json.loads(error.content)
  except ValueError:  # message is not JSON
    return error.content

  code = data['error']['code']
  message = data['error']['message']
  return 'ResponseError {0}: {1}'.format(code, message)


def GetErrorCodeAndMessage(error):
  """Returns the individual error code and message from a JSON http response.

  Prefer using GetError(error) unless you need to examine the error code and
  take specific action on it.

  Args:
    error: the Http error response, whose content is a JSON-format string.

  Returns:
    (code, msg) A tuple holding the error code and error message string.

  Raises:
    ValueError: if the error is not in JSON format.
  """
  data = json.loads(error.content)
  return data['error']['code'], data['error']['message']


def GetProject():
  """Get the user's project id from the core project properties.

  Returns:
    The id of the GCE project to use while running the test.

  Raises:
    MissingProjectError: if the user did not specify a project id via the
      --project flag or via running "gcloud config set project PROJECT_ID".
  """
  project = properties.VALUES.core.project.Get()
  if not project:
    raise exceptions.MissingProjectError(
        'No project specified. Please add --project PROJECT_ID to the command'
        ' line or first run\n  $ gcloud config set project PROJECT_ID')
  return project


def GetDeviceIpBlocks(context=None):
  """Gets the device IP block catalog from the TestEnvironmentDiscoveryService.

  Args:
    context: {str:object}, The current context, which is a set of key-value
      pairs that can be used for common initialization among commands.

  Returns:
    The device IP block catalog

  Raises:
    calliope_exceptions.HttpException: If it could not connect to the service.
  """
  if context:
    client = context['testing_client']
    messages = context['testing_messages']
  else:
    client = apis.GetClientInstance('testing', 'v1')
    messages = apis.GetMessagesModule('testing', 'v1')

  env_type = (
      messages.TestingTestEnvironmentCatalogGetRequest
      .EnvironmentTypeValueValuesEnum.DEVICE_IP_BLOCKS)
  return _GetCatalog(client, messages, env_type).deviceIpBlockCatalog


def GetAndroidCatalog(context=None):
  """Gets the Android catalog from the TestEnvironmentDiscoveryService.

  Args:
    context: {str:object}, The current context, which is a set of key-value
      pairs that can be used for common initialization among commands.

  Returns:
    The android catalog.

  Raises:
    calliope_exceptions.HttpException: If it could not connect to the service.
  """
  if context:
    client = context['testing_client']
    messages = context['testing_messages']
  else:
    client = apis.GetClientInstance('testing', 'v1')
    messages = apis.GetMessagesModule('testing', 'v1')

  env_type = (
      messages.TestingTestEnvironmentCatalogGetRequest.
      EnvironmentTypeValueValuesEnum.ANDROID)
  return _GetCatalog(client, messages, env_type).androidDeviceCatalog


def GetIosCatalog(context=None):
  """Gets the iOS catalog from the TestEnvironmentDiscoveryService.

  Args:
    context: {str:object}, The current context, which is a set of key-value
      pairs that can be used for common initialization among commands.

  Returns:
    The iOS catalog.

  Raises:
    calliope_exceptions.HttpException: If it could not connect to the service.
  """
  if context:
    client = context['testing_client']
    messages = context['testing_messages']
  else:
    client = apis.GetClientInstance('testing', 'v1')
    messages = apis.GetMessagesModule('testing', 'v1')

  env_type = (
      messages.TestingTestEnvironmentCatalogGetRequest.
      EnvironmentTypeValueValuesEnum.IOS)
  return _GetCatalog(client, messages, env_type).iosDeviceCatalog


def GetNetworkProfileCatalog(context=None):
  """Gets the network profile catalog from the TestEnvironmentDiscoveryService.

  Args:
    context: {str:object}, The current context, which is a set of key-value
      pairs that can be used for common initialization among commands.

  Returns:
    The network profile catalog.

  Raises:
    calliope_exceptions.HttpException: If it could not connect to the service.
  """
  if context:
    client = context['testing_client']
    messages = context['testing_messages']
  else:
    client = apis.GetClientInstance('testing', 'v1')
    messages = apis.GetMessagesModule('testing', 'v1')

  env_type = (
      messages.TestingTestEnvironmentCatalogGetRequest.
      EnvironmentTypeValueValuesEnum.NETWORK_CONFIGURATION)
  return _GetCatalog(client, messages, env_type).networkConfigurationCatalog


def _GetCatalog(client, messages, environment_type):
  """Gets a test environment catalog from the TestEnvironmentDiscoveryService.

  Args:
    client: The Testing API client object.
    messages: The Testing API messages object.
    environment_type: {enum} which EnvironmentType catalog to get.

  Returns:
    The test environment catalog.

  Raises:
    calliope_exceptions.HttpException: If it could not connect to the service.
  """
  project_id = properties.VALUES.core.project.Get()
  request = messages.TestingTestEnvironmentCatalogGetRequest(
      environmentType=environment_type,
      projectId=project_id)
  try:
    return client.testEnvironmentCatalog.Get(request)
  except apitools_exceptions.HttpError as error:
    raise calliope_exceptions.HttpException(
        'Unable to access the test environment catalog: ' + GetError(error))
  except:
    # Give the user some explanation in case we get a vague/unexpected error,
    # such as a socket.error from httplib2.
    log.error('Unable to access the Firebase Test Lab environment catalog.')
    raise  # Re-raise the error in case Calliope can do something with it.


def ParseRoboDirectiveKey(key):
  """Returns a tuple representing a directive's type and resource name.

  Args:
    key: the directive key, which can be "<type>:<resource>" or "<resource>"

  Returns:
    A tuple of the directive's parsed type and resource name. If no type is
    specified, "text" will be returned as the default type.

  Raises:
    InvalidArgException: if the input format is incorrect or if the specified
    type is unsupported.
  """

  parts = key.split(':')
  resource_name = parts[-1]
  if len(parts) > 2:
    # Invalid format: at most one ':' is allowed.
    raise exceptions.InvalidArgException(
        'robo_directives', 'Invalid format for key [{0}]. '
        'Use a colon only to separate action type and resource name.'.format(
            key))

  if len(parts) == 1:
    # Format: '<resource_name>=<input_text>' defaults to 'text'
    action_type = 'text'
  else:
    # Format: '<type>:<resource_name>=<input_value>'
    action_type = parts[0]
    supported_action_types = ['text', 'click', 'ignore']
    if action_type not in supported_action_types:
      raise exceptions.InvalidArgException(
          'robo_directives',
          'Unsupported action type [{0}]. Please choose one of [{1}]'.format(
              action_type, ', '.join(supported_action_types)))

  return (action_type, resource_name)


def GetDeprecatedTagWarning(models, platform='android'):
  """Returns a warning string iff any device model is marked deprecated."""
  for model in models:
    for tag in model.tags:
      if 'deprecated' in tag:
        return ('Some devices are deprecated. Learn more at https://firebase.'
                'google.com/docs/test-lab/%s/'
                'available-testing-devices#deprecated' % platform)
  return None


def GetRelativeDevicePath(device_path):
  """Returns the relative device path that can be joined with GCS bucket."""
  return device_path[1:] if device_path.startswith('/') else device_path
