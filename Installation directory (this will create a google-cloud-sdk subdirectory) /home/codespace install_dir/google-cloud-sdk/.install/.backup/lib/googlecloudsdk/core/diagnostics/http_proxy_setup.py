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

"""A module for changing Cloud SDK proxy settings interactively."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import http_proxy_types

import httplib2


def ChangeGcloudProxySettings():
  """Displays proxy information and helps user set up gcloud proxy properties.

  Returns:
    Whether properties were successfully changed.
  """
  try:
    proxy_info, is_existing_proxy = EffectiveProxyInfo()
  except properties.InvalidValueError:
    log.status.Print(
        'Cloud SDK network proxy settings appear to be invalid. Proxy type, '
        'address, and port must be specified. Run [gcloud info] for more '
        'details.\n')
    is_existing_proxy = True
  else:
    _DisplayGcloudProxyInfo(proxy_info, is_existing_proxy)

  if properties.VALUES.core.disable_prompts.GetBool():
    return False

  if is_existing_proxy:
    options = ['Change Cloud SDK network proxy properties',
               'Clear all gcloud proxy properties',
               'Exit']
    existing_proxy_idx = console_io.PromptChoice(
        options, message='What would you like to do?')

    if existing_proxy_idx == 0:
      return _ProxySetupWalkthrough()

    if existing_proxy_idx == 1:
      SetGcloudProxyProperties()
      log.status.Print('Cloud SDK proxy properties cleared.\n')
      return True

    return False
  else:
    if console_io.PromptContinue(prompt_string='Do you have a network proxy '
                                 'you would like to set in gcloud'):
      return _ProxySetupWalkthrough()
    return False


def _ProxySetupWalkthrough():
  """Walks user through setting up gcloud proxy properties."""
  proxy_type_options = sorted(
      t.upper() for t in http_proxy_types.PROXY_TYPE_MAP)
  proxy_type_idx = console_io.PromptChoice(
      proxy_type_options, message='Select the proxy type:')
  if proxy_type_idx is None:
    return False
  proxy_type = proxy_type_options[proxy_type_idx].lower()

  address = console_io.PromptResponse('Enter the proxy host address: ')
  log.status.Print()
  if not address:
    return False

  port = console_io.PromptResponse('Enter the proxy port: ')
  log.status.Print()
  # Restrict port number to 0-65535.
  if not port:
    return False
  try:
    if not 0 <= int(port) <= 65535:
      log.status.Print('Port number must be between 0 and 65535.')
      return False
  except ValueError:
    log.status.Print('Please enter an integer for the port number.')
    return False

  username, password = None, None
  authenticated = console_io.PromptContinue(
      prompt_string='Is your proxy authenticated', default=False)
  if authenticated:
    username = console_io.PromptResponse('Enter the proxy username: ')
    log.status.Print()
    if not username:
      return False
    password = console_io.PromptResponse('Enter the proxy password: ')
    log.status.Print()
    if not password:
      return False

  SetGcloudProxyProperties(proxy_type=proxy_type, address=address, port=port,
                           username=username, password=password)
  log.status.Print('Cloud SDK proxy properties set.\n')
  return True


def EffectiveProxyInfo():
  """Returns ProxyInfo effective in gcloud and if it is from gloud properties.

  Returns:
    A tuple of two elements in which the first element is an httplib2.ProxyInfo
      object and the second is a bool that is True if the proxy info came from
      previously set Cloud SDK proxy properties.

  Raises:
    properties.InvalidValueError: If the properties did not include a valid set.
      "Valid" means all three of these attributes are present: proxy type, host,
      and port.
  """
  proxy_info = http_proxy.GetHttpProxyInfo()  # raises InvalidValueError
  if not proxy_info:
    return None, False

  # googlecloudsdk.core.http_proxy.GetHttpProxyInfo() will return a function
  # if there are no valid proxy settings in gcloud properties. Otherwise, it
  # will return an instantiated httplib2.ProxyInfo object.
  from_gcloud_properties = True
  if not isinstance(proxy_info, httplib2.ProxyInfo):
    from_gcloud_properties = False
    # All Google Cloud SDK network calls use https.
    proxy_info = proxy_info('https')

  return proxy_info, from_gcloud_properties


def _DisplayGcloudProxyInfo(proxy_info, from_gcloud):
  """Displays Cloud SDK proxy information."""
  if not proxy_info:
    log.status.Print()
    return

  log.status.Print('Current effective Cloud SDK network proxy settings:')
  if not from_gcloud:
    log.status.Print('(These settings are from your machine\'s environment, '
                     'not gcloud properties.)')
  proxy_type_name = http_proxy_types.REVERSE_PROXY_TYPE_MAP.get(
      proxy_info.proxy_type, 'UNKNOWN PROXY TYPE')
  log.status.Print('    type = {0}'.format(proxy_type_name))
  log.status.Print('    host = {0}'.format(proxy_info.proxy_host))
  log.status.Print('    port = {0}'.format(proxy_info.proxy_port))
  # In Python 3, httplib2 encodes the proxy username and password when
  # initializing ProxyInfo, so we want to ensure they're decoded here before
  # displaying them.
  log.status.Print('    username = {0}'.format(
      encoding.Decode(proxy_info.proxy_user)))
  log.status.Print('    password = {0}'.format(
      encoding.Decode(proxy_info.proxy_pass)))
  log.status.Print()


def SetGcloudProxyProperties(proxy_type=None, address=None, port=None,
                             username=None, password=None):
  """Sets proxy group properties; clears any property not explicitly set."""
  properties.PersistProperty(properties.VALUES.proxy.proxy_type, proxy_type)
  properties.PersistProperty(properties.VALUES.proxy.address, address)
  properties.PersistProperty(properties.VALUES.proxy.port, port)
  properties.PersistProperty(properties.VALUES.proxy.username, username)
  properties.PersistProperty(properties.VALUES.proxy.password, password)
