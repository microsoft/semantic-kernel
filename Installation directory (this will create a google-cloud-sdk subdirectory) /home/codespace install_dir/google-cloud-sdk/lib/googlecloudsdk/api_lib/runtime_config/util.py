# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Common helper methods for Runtime Config commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import socket

from apitools.base.py import encoding

from googlecloudsdk.api_lib.runtime_config import exceptions as rtc_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as sdk_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry

import six

# The important substring from the error message "The read operation
# timed out".
TIMEOUT_ERR_TEXT = 'read operation timed out'

# The maximum number of seconds that a waiter timeout value can be set to.
# TODO(b/36050879): figure out proper maximum value
MAX_WAITER_TIMEOUT = 60 * 60 * 12  # 12 hours

# Default number of seconds to sleep between checking waiter status.
DEFAULT_WAITER_SLEEP = 5  # 5 seconds

# Length of the prefix before the short variable name.
VARIABLE_NAME_PREFIX_LENGTH = 5


def ProjectPath(project):
  return '/'.join(['projects', project])


def ConfigPath(project, config):
  return '/'.join([ProjectPath(project), 'configs', config])


def VariablePath(project, config, variable):
  return '/'.join([ConfigPath(project, config), 'variables',
                   variable.lstrip('/')])


def WaiterPath(project, config, waiter):
  return '/'.join([ConfigPath(project, config), 'waiters', waiter])


# TODO(b/36050485): these parse functions should live in command_lib.
def ParseConfigName(config_name):
  """Parse a config name or URL, and return a resource.

  Args:
    config_name: The config name.

  Returns:
    The parsed resource.
  """
  params = {
      'projectsId': Project
  }
  return resources.REGISTRY.Parse(config_name,
                                  collection='runtimeconfig.projects.configs',
                                  params=params)


def ParseVariableName(variable_name, args):
  """Parse a variable name or URL, and return a resource.

  Args:
    variable_name: The variable name.
    args: CLI arguments, possibly containing a config name.

  Returns:
    The parsed resource.
  """
  # Parameter values are lazily-evaluated only if they're actually necessary.
  # If the user passes a full URL for the variable name, a separate
  # --config-name parameter is not necessary. Without lazy evaluation,
  # ConfigName function will raise an error if --config-name is unspecified,
  # even if the variable name is a URL.
  params = {
      'projectsId': lambda: ParseConfigName(ConfigName(args)).projectsId,
      'configsId': lambda: ParseConfigName(ConfigName(args)).configsId
  }

  return resources.REGISTRY.Parse(
      variable_name,
      collection='runtimeconfig.projects.configs.variables',
      params=params)


def ParseWaiterName(waiter_name, args):
  """Parse a waiter name or URL, and return a resource.

  Args:
    waiter_name: The waiter name.
    args: CLI arguments, possibly containing a config name.

  Returns:
    The parsed resource.
  """
  params = {
      'projectsId': lambda: ParseConfigName(ConfigName(args)).projectsId,
      'configsId': lambda: ParseConfigName(ConfigName(args)).configsId
  }

  return resources.REGISTRY.Parse(
      waiter_name,
      collection='runtimeconfig.projects.configs.waiters',
      params=params)


def ConfigName(args, required=True):
  if required and not getattr(args, 'config_name', None):
    raise sdk_exceptions.RequiredArgumentException(
        'config', '--config-name parameter is required.')

  return getattr(args, 'config_name', None)


def Client(timeout=None, num_retries=None):
  client = apis.GetClientInstance('runtimeconfig', 'v1beta1')

  if timeout is not None:
    client.http.timeout = timeout
  if num_retries is not None:
    client.num_retries = num_retries

  return client


def ConfigClient(**kwargs):
  return Client(**kwargs).projects_configs


def VariableClient(**kwargs):
  return Client(**kwargs).projects_configs_variables


def WaiterClient(**kwargs):
  return Client(**kwargs).projects_configs_waiters


def Messages():
  return apis.GetMessagesModule('runtimeconfig', 'v1beta1')


def Project(required=True):
  return properties.VALUES.core.project.Get(required=required)


def IsBadGatewayError(error):
  return getattr(error, 'status_code', None) == 502


def IsDeadlineExceededError(error):
  return getattr(error, 'status_code', None) == 504


def IsSocketTimeout(error):
  # For SSL timeouts, the error does not extend socket.timeout.
  # There doesn't appear to be any way to differentiate an SSL
  # timeout from any other SSL error other than checking the
  # message. :(
  return (isinstance(error, socket.timeout)
          or TIMEOUT_ERR_TEXT in six.text_type(error))


def WaitForWaiter(waiter_resource, sleep=None, max_wait=None):
  """Wait for a waiter to finish.

  Args:
    waiter_resource: The waiter resource to wait for.
    sleep: The number of seconds to sleep between status checks.
    max_wait: The maximum number of seconds to wait before an error is raised.

  Returns:
    The last retrieved value of the Waiter.

  Raises:
    WaitTimeoutError: If the wait operation takes longer than the maximum wait
        time.
  """
  sleep = sleep if sleep is not None else DEFAULT_WAITER_SLEEP
  max_wait = max_wait if max_wait is not None else MAX_WAITER_TIMEOUT
  waiter_client = WaiterClient()
  retryer = retry.Retryer(max_wait_ms=max_wait * 1000)

  request = (waiter_client.client.MESSAGES_MODULE
             .RuntimeconfigProjectsConfigsWaitersGetRequest(
                 name=waiter_resource.RelativeName()))

  with progress_tracker.ProgressTracker(
      'Waiting for waiter [{0}] to finish'.format(waiter_resource.Name())):
    try:
      result = retryer.RetryOnResult(waiter_client.Get,
                                     args=[request],
                                     sleep_ms=sleep * 1000,
                                     should_retry_if=lambda w, s: not w.done)
    except retry.WaitException:
      raise rtc_exceptions.WaitTimeoutError(
          'Waiter [{0}] did not finish within {1} seconds.'.format(
              waiter_resource.Name(), max_wait))

  if result.error is not None:
    if result.error.message is not None:
      message = 'Waiter [{0}] finished with an error: {1}'.format(
          waiter_resource.Name(), result.error.message)
    else:
      message = 'Waiter [{0}] finished with an error.'.format(
          waiter_resource.Name())
    log.error(message)

  return result


def IsFailedWaiter(waiter):
  """Returns True if the specified waiter has failed."""
  return waiter.error is not None


def _DictWithShortName(message, name_converter):
  """Returns a dict representation of the message with a shortened name value.

  This method does three things:
  1. converts message to a dict.
  2. shortens the value of the name field using name_converter
  3. sets atomicName to the original value of name.

  Args:
    message: A protorpclite message.
    name_converter: A function that takes an atomic name as a parameter and
        returns a shortened name.

  Returns:
    A dict representation of the message with a shortened name field.

  Raises:
    ValueError: If the original message already contains an atomicName field.
  """
  message_dict = encoding.MessageToDict(message)

  # Defend against the unlikely scenario where the original message
  # already has an 'atomicName' field.
  if 'name' in message_dict:
    if 'atomicName' in message_dict:
      raise ValueError('Original message cannot contain an atomicName field.')

    message_dict['atomicName'] = message_dict['name']
    message_dict['name'] = name_converter(message_dict['name'])

  return message_dict


def FormatConfig(message):
  """Returns the config message as a dict with a shortened name."""
  # Example name:
  #   "projects/my-project/configs/my-config"
  # name.split('/')[-1] returns 'my-config'.
  return _DictWithShortName(message, lambda name: name.split('/')[-1])


def FormatVariable(message, output_value=False):
  """Returns the variable message as a dict with a shortened name.

  This method first converts the variable message to a dict with a shortened
  name and an atomicName. Then, decodes the variable value in the dict if the
  output_value flag is True.

  Args:
    message: A protorpclite message.
    output_value: A bool flag indicates whether we want to decode and output the
        values of the variables. The default value of this flag is False.

  Returns:
    A dict representation of the message with a shortened name field.
  """
  # Example name:
  #   "projects/my-project/configs/my-config/variables/my/var"
  # '/'.join(name.split('/')[5:]) returns 'my/var'
  message_dict = _DictWithShortName(
      message,
      lambda name: '/'.join(name.split('/')[VARIABLE_NAME_PREFIX_LENGTH:]))

  if output_value:
    # A variable always has either a "text" field or a base64-encoded "value"
    # field but not both.
    if 'text' in message_dict:
      message_dict['value'] = message_dict['text']
    else:
      message_dict['value'] = base64.b64decode(message_dict['value'])

  return message_dict


def FormatWaiter(message):
  """Returns the waiter message as a dict with a shortened name."""
  # Example name:
  #   "projects/my-project/configs/my-config/waiters/my-waiter"
  # name.split('/')[-1] returns 'my-waiter'
  return _DictWithShortName(message, lambda name: name.split('/')[-1])
