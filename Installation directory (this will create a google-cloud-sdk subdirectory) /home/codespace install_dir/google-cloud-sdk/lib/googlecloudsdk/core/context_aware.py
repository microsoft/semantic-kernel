# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Helper module for context aware access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import atexit
import enum
import json
import os

from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import _mtls_helper
from googlecloudsdk.command_lib.auth import enterprise_certificate_config
from googlecloudsdk.core import argv_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
import six


CONTEXT_AWARE_ACCESS_DENIED_ERROR = 'access_denied'
CONTEXT_AWARE_ACCESS_DENIED_ERROR_DESCRIPTION = 'Account restricted'
CONTEXT_AWARE_ACCESS_HELP_MSG = (
    'Access was blocked due to an organization policy, please contact your '
    'admin to gain access.'
)


def IsContextAwareAccessDeniedError(exc):
  exc_text = six.text_type(exc)
  return (CONTEXT_AWARE_ACCESS_DENIED_ERROR in exc_text and
          CONTEXT_AWARE_ACCESS_DENIED_ERROR_DESCRIPTION in exc_text)


DEFAULT_AUTO_DISCOVERY_FILE_PATH = os.path.join(
    files.GetHomeDir(), '.secureConnect', 'context_aware_metadata.json')


def _AutoDiscoveryFilePath():
  """Return the file path of the context aware configuration file."""
  # auto_discovery_file_path is an override used for testing purposes.
  cfg_file = properties.VALUES.context_aware.auto_discovery_file_path.Get()
  if cfg_file is not None:
    return cfg_file
  return DEFAULT_AUTO_DISCOVERY_FILE_PATH


class ConfigException(exceptions.Error):

  def __init__(self):
    super(ConfigException, self).__init__(
        'Use of client certificate requires endpoint verification agent. '
        'Run `gcloud topic client-certificate` for installation guide.')


class CertProvisionException(exceptions.Error):
  """Represents errors when provisioning a client certificate."""
  pass


def SSLCredentials(config_path):
  """Generates the client SSL credentials.

  Args:
    config_path: path to the context aware configuration file.

  Raises:
    CertProvisionException: if the cert could not be provisioned.
    ConfigException: if there is an issue in the context aware config.

  Returns:
    Tuple[bytes, bytes]: client certificate and private key bytes in PEM format.
  """
  try:
    (
        has_cert,
        cert_bytes,
        key_bytes,
        _
    ) = _mtls_helper.get_client_ssl_credentials(
        generate_encrypted_key=False,
        context_aware_metadata_path=config_path)
    if has_cert:
      return cert_bytes, key_bytes
  except google_auth_exceptions.ClientCertError as caught_exc:
    new_exc = CertProvisionException(caught_exc)
    six.raise_from(new_exc, caught_exc)
  raise ConfigException()


def EncryptedSSLCredentials(config_path):
  """Generates the encrypted client SSL credentials.

  The encrypted client SSL credentials are stored in a file which is returned
  along with the password.

  Args:
    config_path: path to the context aware configuration file.

  Raises:
    CertProvisionException: if the cert could not be provisioned.
    ConfigException: if there is an issue in the context aware config.

  Returns:
    Tuple[str, bytes]: cert and key file path and passphrase bytes.
  """
  try:
    (
        has_cert,
        cert_bytes,
        key_bytes,
        passphrase_bytes
    ) = _mtls_helper.get_client_ssl_credentials(
        generate_encrypted_key=True,
        context_aware_metadata_path=config_path)
    if has_cert:
      cert_path = os.path.join(
          config.Paths().global_config_dir, 'caa_cert.pem')
      with files.BinaryFileWriter(cert_path) as f:
        f.write(cert_bytes)
        f.write(key_bytes)
      return cert_path, passphrase_bytes
  except google_auth_exceptions.ClientCertError as caught_exc:
    new_exc = CertProvisionException(caught_exc)
    six.raise_from(new_exc, caught_exc)
  except files.Error as e:
    log.debug('context aware settings discovery file %s - %s', config_path, e)

  raise ConfigException()


def _ShouldRepairECP(cert_config):
  """Check if ECP binaries should be installed and the ECP config updated to point to them."""
  # Skip repair if gcloud init is the command. This avoids mangling the wizard
  # due to starting the component manager.
  args = argv_utils.GetDecodedArgv()
  if 'init' in args:
    return False

  if 'cert_configs' not in cert_config:
    return False

  if len(cert_config['cert_configs'].keys()) < 1:
    return False

  if 'libs' not in cert_config:
    return False

  expected_keys = set(['ecp', 'ecp_client', 'tls_offload'])
  actual_keys = set(cert_config['libs'].keys())

  if expected_keys == actual_keys:
    return False

  return True


def _GetPlatform():
  platform = platforms.Platform.Current()
  if (
      platform.operating_system == platforms.OperatingSystem.MACOSX
      and platform.architecture == platforms.Architecture.x86_64
  ):
    if platforms.Platform.IsActuallyM1ArmArchitecture():
      platform.architecture = platforms.Architecture.arm

  return platform


def _RepairECP(cert_config_file_path):
  """Install ECP and update the ecp config to include the new binaries.

  Args:
    cert_config_file_path: The filepath of the active certificate config.

  See go/gcloud-ecp-repair.
  """
  # Temporarily disable client certificate to avoid deadlock.
  properties.VALUES.context_aware.use_client_certificate.Set(False)

  # Update manager depends on Context Aware, so cannot import it at the top.
  from googlecloudsdk.core.updater import update_manager  # pylint:disable=g-import-not-at-top

  platform = _GetPlatform()
  updater = update_manager.UpdateManager(
      sdk_root=None, url=None, platform_filter=platform
  )

  already_installed = updater.EnsureInstalledAndRestart(
      ['enterprise-certificate-proxy'],
      'Device appears to be enrolled in Certificate Base Access but is missing'
      ' criticial components. Installing enterprise-certificate-proxy and'
      ' restarting gcloud.',
  )

  if already_installed:
    enterprise_certificate_config.update_config(
        enterprise_certificate_config.platform_to_config(platform),
        output_file=cert_config_file_path,
    )
    properties.VALUES.context_aware.use_client_certificate.Set(True)


def _GetCertificateConfigFile():
  """Validates and returns the certificate config file path."""

  # First see if there is a config file.
  file_path = properties.VALUES.context_aware.certificate_config_file_path.Get()
  if file_path is None:
    file_path = config.CertConfigDefaultFilePath()

  if not os.path.exists(file_path):
    return None

  # Make sure the config file is a valid JSON file.
  try:
    content = files.ReadFileContents(file_path)
    cert_config = json.loads(content)
  except ValueError as caught_exc:
    new_exc = CertProvisionException(
        'The enterprise certificate config file is not a valid JSON file',
        caught_exc,
    )
    six.raise_from(new_exc, caught_exc)
  except files.Error as caught_exc:
    new_exc = CertProvisionException(
        'Failed to read enterprise certificate config file', caught_exc
    )
    six.raise_from(new_exc, caught_exc)

  # Check if the config file contains the ecp binary path.
  # If ecp binary path is provided but the binary doesn't exist, throw
  # exception
  if (
      'libs' in cert_config
      and 'ecp' in cert_config['libs']
      and not os.path.exists(cert_config['libs']['ecp'])
  ):
    raise CertProvisionException(
        'Enterprise certificate provider (ECP) binary path'
        ' (cert_config["libs"]["ecp"]) specified in enterprise certificate'
        ' config file was not found. Cannot use mTLS with ECP if the ECP binary'
        ' does not exist. Please check the ECP configuration. See `gcloud topic'
        ' client-certificate` to learn more about ECP. \nIf this error is'
        ' unexpected either delete {} or generate a new configuration with `$'
        ' gcloud auth enterprise-certificate-config create --help` '.format(
            file_path
        )
    )

  if _ShouldRepairECP(cert_config):
    _RepairECP(file_path)

  return file_path


class ConfigType(enum.Enum):
  ENTERPRISE_CERTIFICATE = 1
  ON_DISK_CERTIFICATE = 2


class _ConfigImpl(object):
  """Represents the configurations associated with context aware access.

  Both the encrypted and unencrypted certs need to be generated to support HTTP
  API clients and gRPC API clients, respectively.

  Only one instance of Config can be created for the program.
  """

  @classmethod
  def Load(cls):
    """Loads the context aware config."""
    if not properties.VALUES.context_aware.use_client_certificate.GetBool():
      return None

    certificate_config_file_path = _GetCertificateConfigFile()
    if certificate_config_file_path:
      # The enterprise cert config file path will be used.
      log.debug('enterprise certificate is used for mTLS')
      return _EnterpriseCertConfigImpl(certificate_config_file_path)

    log.debug('on disk certificate is used for mTLS')
    config_path = _AutoDiscoveryFilePath()
    # Raw cert and key
    cert_bytes, key_bytes = SSLCredentials(config_path)

    # Encrypted cert stored in a file
    encrypted_cert_path, password = EncryptedSSLCredentials(config_path)
    return _OnDiskCertConfigImpl(config_path, cert_bytes, key_bytes,
                                 encrypted_cert_path, password)

  def __init__(self, config_type):
    self.config_type = config_type


class _EnterpriseCertConfigImpl(_ConfigImpl):
  """Represents the configurations associated with context aware access through a enterprise certificate on TPM or OS key store."""

  def __init__(self, certificate_config_file_path):
    super(_EnterpriseCertConfigImpl,
          self).__init__(ConfigType.ENTERPRISE_CERTIFICATE)
    self.certificate_config_file_path = certificate_config_file_path


class _OnDiskCertConfigImpl(_ConfigImpl):
  """Represents the configurations associated with context aware access through a certificate on disk.

  Both the encrypted and unencrypted certs need to be generated to support HTTP
  API clients and gRPC API clients, respectively.

  Only one instance of Config can be created for the program.
  """

  def __init__(self, config_path, client_cert_bytes, client_key_bytes,
               encrypted_client_cert_path, encrypted_client_cert_password):
    super(_OnDiskCertConfigImpl, self).__init__(ConfigType.ON_DISK_CERTIFICATE)
    self.config_path = config_path
    self.client_cert_bytes = client_cert_bytes
    self.client_key_bytes = client_key_bytes
    self.encrypted_client_cert_path = encrypted_client_cert_path
    self.encrypted_client_cert_password = encrypted_client_cert_password
    atexit.register(self.CleanUp)

  def CleanUp(self):
    """Cleanup any files or resource provisioned during config init."""
    if (self.encrypted_client_cert_path is not None and
        os.path.exists(self.encrypted_client_cert_path)):
      try:
        os.remove(self.encrypted_client_cert_path)
        log.debug('unprovisioned client cert - %s',
                  self.encrypted_client_cert_path)
      except files.Error as e:
        log.error('failed to remove client certificate - %s', e)


singleton_config = None


def Config():
  """Represents the configurations associated with context aware access."""
  global singleton_config
  if not singleton_config:
    singleton_config = _ConfigImpl.Load()

  return singleton_config
