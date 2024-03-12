# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Create ECP configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import json
import os

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

RESOURCE_TYPE = 'enterprise-certificate-proxy configuration file'


def get_platform_folder():
  sdk_root = config.Paths().sdk_root
  if not sdk_root:
    raise ECPConfigError(
        'Unable to find the SDK root path. The gcloud installation may be'
        ' corrupted.'
    )

  return os.path.join(sdk_root, 'platform', 'enterprise_cert')


def get_bin_folder():
  sdk_bin_path = config.Paths().sdk_bin_path
  if not sdk_bin_path:
    raise ECPConfigError(
        'Unable to find the SDK bin path. The gcloud installation may be'
        ' corrupted.'
    )

  return sdk_bin_path


def get_config_path(output_file):
  if output_file:
    return output_file
  return config.CertConfigDefaultFilePath()


def platform_to_config(platform):
  if not platform:
    platform = platforms.Platform.Current()
  if platform.operating_system == platforms.OperatingSystem.MACOSX:
    return ConfigType.KEYCHAIN
  elif platform.operating_system == platforms.OperatingSystem.LINUX:
    return ConfigType.PKCS11
  elif platform.operating_system == platforms.OperatingSystem.WINDOWS:
    return ConfigType.MYSTORE
  else:
    raise ECPConfigError(
        (
            'Unsupported platform {}. Enterprise Certificate Proxy currently'
            ' only supports OSX, Windows, and Linux.'
        ).format(platform.operating_system)
    )


class ConfigType(enum.Enum):
  PKCS11 = 1
  KEYCHAIN = 2
  MYSTORE = 3


class WindowsBinaryPathConfig(object):

  def __init__(self, ecp, ecp_client, tls_offload):
    self.ecp = ecp if ecp else os.path.join(get_bin_folder(), 'ecp.exe')
    self.ecp_client = (
        ecp_client
        if ecp_client
        else os.path.join(get_platform_folder(), 'libecp.dll')
    )
    self.tls_offload = (
        tls_offload
        if tls_offload
        else os.path.join(get_platform_folder(), 'libtls_offload.dll')
    )


class LinuxPathConfig(object):

  def __init__(self, ecp, ecp_client, tls_offload):
    self.ecp = ecp if ecp else os.path.join(get_bin_folder(), 'ecp')
    self.ecp_client = (
        ecp_client
        if ecp_client
        else os.path.join(get_platform_folder(), 'libecp.so')
    )
    self.tls_offload = (
        tls_offload
        if tls_offload
        else os.path.join(get_platform_folder(), 'libtls_offload.so')
    )


class MacOSBinaryPathConfig(object):

  def __init__(self, ecp, ecp_client, tls_offload):
    self.ecp = ecp if ecp else os.path.join(get_bin_folder(), 'ecp')
    self.ecp_client = (
        ecp_client
        if ecp_client
        else os.path.join(get_platform_folder(), 'libecp.dylib')
    )
    self.tls_offload = (
        tls_offload
        if tls_offload
        else os.path.join(get_platform_folder(), 'libtls_offload.dylib')
    )


class PKCS11Config(object):

  def __init__(self, module, slot, label, user_pin):
    self.module = module
    self.slot = slot
    self.label = label

    if user_pin:
      self.user_pin = user_pin


class KeyChainConfig(object):

  def __init__(self, issuer):
    self.issuer = issuer


class MyStoreConfig(object):

  def __init__(self, issuer, store, provider):
    self.issuer = issuer
    self.store = store
    self.provider = provider


def create_linux_config(base_config, **kwargs):
  """Creates a Linux ECP Config.

  Args:
    base_config: Optional parameter to use as a fallback for parameters that are
      not set in kwargs.
    **kwargs: Linux config parameters. See go/enterprise-cert-config for valid
      variables.

  Returns:
    A dictionary object containing the ECP config.
  """
  if base_config:
    base_linux_config = base_config.get('cert_configs', {}).get('pkcs11', {})
    base_libs_config = base_config.get('libs', {})
  else:
    base_linux_config = {}
    base_libs_config = {}

  ecp_config = PKCS11Config(
      kwargs.get('module', None) or base_linux_config.get('module', None),
      kwargs.get('slot', None) or base_linux_config.get('slot', 0),
      kwargs.get('label', None) or base_linux_config.get('label', None),
      kwargs.get('user_pin', None) or base_linux_config.get('user_pin', None),
  )
  lib_config = LinuxPathConfig(
      kwargs.get('ecp', None) or base_libs_config.get('ecp', None),
      kwargs.get('ecp_client', None)
      or base_libs_config.get('ecp_client', None),
      kwargs.get('tls_offload', None)
      or base_libs_config.get('tls_offload', None),
  )
  return {'pkcs11': vars(ecp_config)}, {'libs': vars(lib_config)}


def create_macos_config(base_config, **kwargs):
  """Creates a MacOS ECP Config.

  Args:
    base_config: Optional parameter to use as a fallback for parameters that are
      not set in kwargs.
    **kwargs: MacOS config parameters. See go/enterprise-cert-config for valid
      variables.

  Returns:
    A dictionary object containing the ECP config.
  """
  if base_config:
    base_macos_config = base_config['cert_configs']['macos_keychain']
    base_libs_config = base_config['libs']
  else:
    base_macos_config = {}
    base_libs_config = {}

  ecp_config = KeyChainConfig(
      kwargs.get('issuer', None) or base_macos_config.get('issuer', None)
  )
  lib_config = MacOSBinaryPathConfig(
      kwargs.get('ecp', None) or base_libs_config.get('ecp', None),
      kwargs.get('ecp_client', None)
      or base_libs_config.get('ecp_client', None),
      kwargs.get('tls_offload', None)
      or base_libs_config.get('tls_offload', None),
  )
  return {'macos_keychain': vars(ecp_config)}, {'libs': vars(lib_config)}


def create_windows_config(base_config, **kwargs):
  """Creates a Windows ECP Config.

  Args:
    base_config: Optional parameter to use as a fallback for parameters that are
      not set in kwargs.
    **kwargs: Windows config parameters. See go/enterprise-cert-config for valid
      variables.

  Returns:
    A dictionary object containing the ECP config.
  """
  if base_config:
    base_windows_config = base_config['cert_configs']['windows_store']
    base_libs_config = base_config['libs']
  else:
    base_windows_config = {}
    base_libs_config = {}

  ecp_config = MyStoreConfig(
      kwargs.get('issuer', None) or base_windows_config.get('issuer', None),
      kwargs.get('store', None) or base_windows_config.get('store', None),
      kwargs.get('provider', None) or base_windows_config.get('provider', None),
  )
  lib_config = WindowsBinaryPathConfig(
      kwargs.get('ecp', None) or base_libs_config.get('ecp', None),
      kwargs.get('ecp_client', None)
      or base_libs_config.get('ecp_client', None),
      kwargs.get('tls_offload', None)
      or base_libs_config.get('tls_offload', None),
  )
  return {'windows_store': vars(ecp_config)}, {'libs': vars(lib_config)}


def create_ecp_config(config_type, base_config=None, **kwargs):
  """Creates an ECP Config.

  Args:
    config_type: An ConfigType Enum that describes the type of ECP config.
    base_config: Optional parameter to use as a fallback for parameters that are
      not set in kwargs.
    **kwargs: config parameters. See go/enterprise-cert-config for valid
      variables.

  Returns:
    A dictionary object containing the ECP config.
  Raises:
    ECPConfigError: No valid config_type is specified.
  """

  if config_type == ConfigType.PKCS11:
    ecp_config, libs_config = create_linux_config(base_config, **kwargs)
  elif config_type == ConfigType.KEYCHAIN:
    ecp_config, libs_config = create_macos_config(base_config, **kwargs)
  elif config_type == ConfigType.MYSTORE:
    ecp_config, libs_config = create_windows_config(base_config, **kwargs)
  else:
    raise ECPConfigError(
        (
            'Unknown config_type {} passed to create enterprise certificate'
            ' configuration. Valid options are: [PKCS11, KEYCHAIN, MYSTORE]'
        ).format(config_type)
    )
  return {'cert_configs': ecp_config, **libs_config}


def create_config(config_type, **kwargs):
  """Creates the ECP config based on the passed in CLI arguments."""
  output = create_ecp_config(config_type, None, **kwargs)
  config_path = get_config_path(kwargs.get('output_file', None))

  files.WriteFileContents(config_path, json.dumps(output, indent=2))
  log.CreatedResource(config_path, RESOURCE_TYPE)


def update_config(config_type, **kwargs):
  """Updates the ECP config based on the passed in CLI arguments.

  Args:
    config_type: An ConfigType Enum that describes the type of ECP config.
    **kwargs: config parameters that will be updated. See
      go/enterprise-cert-config for valid variables.

  Only explicit args will overwrite existing values
  """
  config_path = get_config_path(kwargs.get('output_file', None))
  data = files.ReadFileContents(config_path)

  active_config = json.loads(data)
  output = create_ecp_config(config_type, active_config, **kwargs)

  files.WriteFileContents(config_path, json.dumps(output, indent=2))
  log.CreatedResource(config_path, RESOURCE_TYPE)


class ECPConfigError(Exception):

  def __init__(self, message):
    super(ECPConfigError, self).__init__()
    self.message = message
