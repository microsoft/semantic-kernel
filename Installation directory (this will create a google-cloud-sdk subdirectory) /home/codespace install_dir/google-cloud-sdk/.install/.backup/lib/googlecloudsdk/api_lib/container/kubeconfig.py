# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Utilities for loading and parsing kubeconfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import subprocess

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms


class Error(core_exceptions.Error):
  """Class for errors raised by kubeconfig utilities."""


class MissingEnvVarError(Error):
  """An exception raised when required environment variables are missing."""


class DNSEndpointOrUseApplicationDefaultCredentialsError(Error):
  """Error for retrieving DNSEndpoint of a cluster that has none."""

  def __init__(self):
    super(DNSEndpointOrUseApplicationDefaultCredentialsError, self).__init__(
        'Only one of --dns-endpoint or USE_APPLICATION_DEFAULT_CREDENTIALS'
        ' should be set at a time.'
    )

GKE_GCLOUD_AUTH_PLUGIN_CACHE_FILE_NAME = 'gke_gcloud_auth_plugin_cache'


class Kubeconfig(object):
  """Interface for interacting with a kubeconfig file."""

  def __init__(self, raw_data, filename):
    self._filename = filename
    self._data = raw_data
    self.clusters = {}
    self.users = {}
    self.contexts = {}
    for cluster in self._data['clusters']:
      self.clusters[cluster['name']] = cluster
    for user in self._data['users']:
      self.users[user['name']] = user
    for context in self._data['contexts']:
      self.contexts[context['name']] = context

  @property
  def current_context(self):
    return self._data['current-context']

  @property
  def filename(self):
    return self._filename

  def Clear(self, key):
    self.contexts.pop(key, None)
    self.clusters.pop(key, None)
    self.users.pop(key, None)
    if self._data.get('current-context') == key:
      self._data['current-context'] = ''

  def SaveToFile(self):
    """Save kubeconfig to file.

    Raises:
      Error: don't have the permission to open kubeconfig or plugin cache file.
    """
    self._data['clusters'] = list(self.clusters.values())
    self._data['users'] = list(self.users.values())
    self._data['contexts'] = list(self.contexts.values())
    with file_utils.FileWriter(self._filename, private=True) as fp:
      yaml.dump(self._data, fp)

    # GKE_GCLOUD_AUTH_PLUGIN_CACHE_FILE_NAME is used by GKE_GCLOUD_AUTH_PLUGIN
    # Erase cache file everytime kubeconfig is updated. This allows for a reset
    # of the cache. Previously, credentials were cached in the kubeconfig file
    # and updating the kubeconfig allowed for a "reset" of the cache.
    dirname = os.path.dirname(self._filename)
    gke_gcloud_auth_plugin_file_path = os.path.join(
        dirname, GKE_GCLOUD_AUTH_PLUGIN_CACHE_FILE_NAME)
    if os.path.exists(gke_gcloud_auth_plugin_file_path):
      file_utils.WriteFileAtomically(gke_gcloud_auth_plugin_file_path, '')

  def SetCurrentContext(self, context):
    self._data['current-context'] = context

  @classmethod
  def _Validate(cls, data):
    """Make sure we have the main fields of a kubeconfig."""
    if not data:
      raise Error('empty file')
    try:
      for key in ('clusters', 'users', 'contexts'):
        if not isinstance(data[key], list):
          raise Error(
              'invalid type for {0}: {1}'.format(data[key], type(data[key])))
    except KeyError as error:
      raise Error('expected key {0} not found'.format(error))

  @classmethod
  def LoadFromFile(cls, filename):
    try:
      data = yaml.load_path(filename)
    except yaml.Error as error:
      raise Error('unable to load kubeconfig for {0}: {1}'.format(
          filename, error.inner_error))
    cls._Validate(data)
    return cls(data, filename)

  @classmethod
  def LoadOrCreate(cls, path):
    """Read in the kubeconfig, and if it doesn't exist create one there."""
    if os.path.isdir(path):
      raise IsADirectoryError(
          '{0} is a directory. File must be provided.'.format(path)
      )
    if os.path.isfile(path):
      try:
        return cls.LoadFromFile(path)
      except (Error, IOError) as error:
        log.debug(
            'unable to load default kubeconfig: {0}; recreating {1}'.format(
                error, path
            )
        )
    file_utils.MakeDir(os.path.dirname(path))
    kubeconfig = cls(EmptyKubeconfig(), path)
    kubeconfig.SaveToFile()
    return kubeconfig

  @classmethod
  def Default(cls):
    return cls.LoadOrCreate(Kubeconfig.DefaultPath())

  @staticmethod
  def DefaultPath():
    """Return default path for kubeconfig file."""

    kubeconfig = encoding.GetEncodedValue(os.environ, 'KUBECONFIG')
    if kubeconfig:
      kubeconfigs = kubeconfig.split(os.pathsep)
      for kubeconfig in kubeconfigs:
        # KUBEONCIFG=$KUBECONFIG:~/.kube/config might be ':~/.kube/config'
        if kubeconfig:
          return os.path.abspath(kubeconfig)

    # This follows the same resolution process as kubectl for the config file.
    home_dir = encoding.GetEncodedValue(os.environ, 'HOME')
    if not home_dir and platforms.OperatingSystem.IsWindows():
      home_drive = encoding.GetEncodedValue(os.environ, 'HOMEDRIVE')
      home_path = encoding.GetEncodedValue(os.environ, 'HOMEPATH')
      if home_drive and home_path:
        home_dir = os.path.join(home_drive, home_path)
      if not home_dir:
        home_dir = encoding.GetEncodedValue(os.environ, 'USERPROFILE')

    if not home_dir:
      raise MissingEnvVarError(
          'environment variable {vars} or KUBECONFIG must be set to store '
          'credentials for kubectl'.format(
              vars='HOMEDRIVE/HOMEPATH, USERPROFILE, HOME,'
              if platforms.OperatingSystem.IsWindows() else 'HOME'))
    return os.path.join(home_dir, '.kube', 'config')

  def Merge(self, kubeconfig):
    """Merge another kubeconfig into self.

    In case of overlapping keys, the value in self is kept and the value in
    the other kubeconfig is lost.

    Args:
      kubeconfig: a Kubeconfig instance
    """
    self.SetCurrentContext(self.current_context or kubeconfig.current_context)
    self.clusters = dict(
        list(kubeconfig.clusters.items()) + list(self.clusters.items()))
    self.users = dict(
        list(kubeconfig.users.items()) + list(self.users.items()))
    self.contexts = dict(
        list(kubeconfig.contexts.items()) + list(self.contexts.items()))


def Cluster(name, server, ca_path=None, ca_data=None, has_dns_endpoint=False):
  """Generate and return a cluster kubeconfig object."""
  cluster = {
      'server': server,
  }
  if ca_path and ca_data:
    raise Error('cannot specify both ca_path and ca_data')
  if ca_path:
    cluster['certificate-authority'] = ca_path
  elif ca_data is not None and not has_dns_endpoint:
    cluster['certificate-authority-data'] = ca_data
  elif not has_dns_endpoint:
    cluster['insecure-skip-tls-verify'] = True
  return {
      'name': name,
      'cluster': cluster
  }


def User(name,
         auth_provider=None,
         auth_provider_cmd_path=None,
         auth_provider_cmd_args=None,
         auth_provider_expiry_key=None,
         auth_provider_token_key=None,
         cert_path=None,
         cert_data=None,
         key_path=None,
         key_data=None,
         dns_endpoint=None):
  """Generates and returns a user kubeconfig object.

  Args:
    name: str, nickname for this user entry.
    auth_provider: str, authentication provider.
    auth_provider_cmd_path: str, authentication provider command path.
    auth_provider_cmd_args: str, authentication provider command args.
    auth_provider_expiry_key: str, authentication provider expiry key.
    auth_provider_token_key: str, authentication provider token key.
    cert_path: str, path to client certificate file.
    cert_data: str, base64 encoded client certificate data.
    key_path: str, path to client key file.
    key_data: str, base64 encoded client key data.
    dns_endpoint: str, cluster's DNS endpoint.
  Returns:
    dict, valid kubeconfig user entry.

  Raises:
    Error: if no auth info is provided (auth_provider or cert AND key)
  """
  # TODO(b/70856999) Figure out what the correct behavior for client certs is.
  if not (auth_provider or (cert_path and key_path) or
          (cert_data and key_data)):
    raise Error('either auth_provider or cert & key must be provided')
  user = {}
  use_exec_auth = _UseExecAuth()

  if auth_provider:
    # Setup authprovider
    # if certain 'auth_provider_' fields are "present" OR
    # if use_exec_auth is set to False
    # pylint: disable=line-too-long
    if auth_provider_cmd_path or auth_provider_cmd_args or auth_provider_expiry_key or auth_provider_token_key or not use_exec_auth:
      # auth-provider is being deprecated in favor of "exec" in k8s 1.25.
      user['auth-provider'] = _AuthProvider(
          name=auth_provider,
          cmd_path=auth_provider_cmd_path,
          cmd_args=auth_provider_cmd_args,
          expiry_key=auth_provider_expiry_key,
          token_key=auth_provider_token_key)
    else:
      user['exec'] = _ExecAuthPlugin(dns_endpoint)

  if cert_path and cert_data:
    raise Error('cannot specify both cert_path and cert_data')
  if cert_path:
    user['client-certificate'] = cert_path
  elif cert_data:
    user['client-certificate-data'] = cert_data

  if key_path and key_data:
    raise Error('cannot specify both key_path and key_data')
  if key_path:
    user['client-key'] = key_path
  elif key_data:
    user['client-key-data'] = key_data

  return {
      'name': name,
      'user': user
  }


def _UseExecAuth():
  """Returns a bool noting if ExecAuth should be enabled.

  Returns:
    bool, which notes if ExecAuth should be enabled
  """
  # Enable ExecAuth for all users
  use_exec_auth = True

  use_gke_gcloud_auth_plugin = encoding.GetEncodedValue(
      os.environ, 'USE_GKE_GCLOUD_AUTH_PLUGIN')
  # if use_gke_gcloud_auth_plugin is explicitly set(True/False), take action.
  # if use_gke_gcloud_auth_plugin is NOT explicitly set, do nothing
  if use_gke_gcloud_auth_plugin and use_gke_gcloud_auth_plugin.lower(
  ) == 'true':
    use_exec_auth = True
  elif use_gke_gcloud_auth_plugin and use_gke_gcloud_auth_plugin.lower(
  ) == 'false':
    use_exec_auth = False

  return use_exec_auth

SDK_BIN_PATH_NOT_FOUND = '''\
Path to sdk installation not found. Please switch to application default
credentials using one of

$ gcloud config set container/use_application_default_credentials true
$ export CLOUDSDK_CONTAINER_USE_APPLICATION_DEFAULT_CREDENTIALS=true'''

GKE_GCLOUD_AUTH_INSTALL_HINT = """\
Install gke-gcloud-auth-plugin for use with kubectl by following \
https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl#install_plugin"""

GKE_GCLOUD_AUTH_PLUGIN_NOT_FOUND = """\
ACTION REQUIRED: gke-gcloud-auth-plugin, \
which is needed for continued use of kubectl, was not found or is not executable. \
""" + GKE_GCLOUD_AUTH_INSTALL_HINT


def _ExecAuthPlugin(dns_endpoint=None):
  """Generate and return an exec auth plugin config.

  Constructs an exec auth plugin config entry readable by kubectl.
  This tells kubectl to call out to gke-gcloud-auth-plugin and
  parse the output to retrieve access tokens to authenticate to
  the kubernetes master.

  Kubernetes GKE Auth Provider plugin is defined at
  https://kubernetes.io/docs/reference/access-authn-authz/authentication/#client-go-credential-plugins

  GKE GCloud Exec Auth Plugin code is at
  https://github.com/kubernetes/cloud-provider-gcp/tree/master/cmd/gke-gcloud-auth-plugin

  Args:
    dns_endpoint: str, DNS endpoint.
  Returns:
    dict, valid exec auth plugin config entry.
  Raises:
    Error: Only one of --dns-endpoint or USE_APPLICATION_DEFAULT_CREDENTIALS
    should be set at a time.
  """

  use_application_default_credentials = (
      properties.VALUES.container.use_app_default_credentials.GetBool()
  )
  if dns_endpoint and use_application_default_credentials:
    raise DNSEndpointOrUseApplicationDefaultCredentialsError()

  command = _GetGkeGcloudPluginCommandAndPrintWarning()

  exec_cfg = {
      'command': command,
      'apiVersion': 'client.authentication.k8s.io/v1beta1',
      'installHint': GKE_GCLOUD_AUTH_INSTALL_HINT,
      'provideClusterInfo': True,
  }

  if use_application_default_credentials:
    exec_cfg['args'] = ['--use_application_default_credentials']
  return exec_cfg


def _AuthProvider(name='gcp',
                  cmd_path=None,
                  cmd_args=None,
                  expiry_key=None,
                  token_key=None):
  """Generates and returns an auth provider config.

  Constructs an auth provider config entry readable by kubectl. This tells
  kubectl to call out to a specific gcloud command and parse the output to
  retrieve access tokens to authenticate to the kubernetes master.
  Kubernetes gcp auth provider plugin at
  https://github.com/kubernetes/kubernetes/tree/master/staging/src/k8s.io/client-go/plugin/pkg/client/auth/gcp

  Args:
    name: auth provider name
    cmd_path: str, authentication provider command path.
    cmd_args: str, authentication provider command arguments.
    expiry_key: str, authentication provider expiry key.
    token_key: str, authentication provider token key.

  Returns:
    dict, valid auth provider config entry.
  Raises:
    Error: Path to sdk installation not found. Please switch to application
    default credentials using one of

    $ gcloud config set container/use_application_default_credentials true
    $ export CLOUDSDK_CONTAINER_USE_APPLICATION_DEFAULT_CREDENTIALS=true.
  """
  provider = {'name': name}
  if (name == 'gcp' and not
      properties.VALUES.container.use_app_default_credentials.GetBool()):
    bin_name = 'gcloud'
    if platforms.OperatingSystem.IsWindows():
      bin_name = 'gcloud.cmd'

    if cmd_path is None:
      sdk_bin_path = config.Paths().sdk_bin_path
      if sdk_bin_path is None:
        log.error(SDK_BIN_PATH_NOT_FOUND)
        raise Error(SDK_BIN_PATH_NOT_FOUND)
      cmd_path = os.path.join(sdk_bin_path, bin_name)
      try:
        # Print warning if gke-gcloud-auth-plugin is not present or executable
        _GetGkeGcloudPluginCommandAndPrintWarning()
      except Exception:  # pylint: disable=broad-except
        # Catch all exceptions to avoid any failures in this code path and
        # ignore the exceptions, as no action needs to be taken.
        pass

    cfg = {
        # Command for gcloud credential helper
        'cmd-path':
            cmd_path,
        # Args for gcloud credential helper
        'cmd-args':
            cmd_args if cmd_args else 'config config-helper --format=json',
        # JSONpath to the field that is the raw access token
        'token-key':
            token_key if token_key else '{.credential.access_token}',
        # JSONpath to the field that is the expiration timestamp
        'expiry-key':
            expiry_key if expiry_key else '{.credential.token_expiry}'
        # Note: we're omitting 'time-fmt' field, which if provided, is a
        # format string of the golang reference time. It can be safely omitted
        # because config-helper's default time format is RFC3339, which is the
        # same default kubectl assumes.
    }
    provider['config'] = cfg
  return provider


def _GetGkeGcloudPluginCommandAndPrintWarning():
  """Get Gke Gcloud Plugin Command to be used.

  Returns Gke Gcloud Plugin Command to be used. Also,
  prints warning if plugin is not present or doesn't work correctly.

  Returns:
    string, Gke Gcloud Plugin Command to be used.
  """
  bin_name = 'gke-gcloud-auth-plugin'
  if platforms.OperatingSystem.IsWindows():
    bin_name = 'gke-gcloud-auth-plugin.exe'
  command = bin_name

  # Check if command is in PATH and executable. Else, print critical(RED)
  # warning as kubectl will break if command is not executable.
  try:
    subprocess.run([command, '--version'],
                   timeout=5,
                   check=False,
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
  except Exception:  # pylint: disable=broad-except
    # Provide SDK Full path if command is not in PATH. This helps work
    # around scenarios where cloud-sdk install location is not in PATH
    # as sdk was installed using other distributions methods Eg: brew
    try:
      # config.Paths().sdk_bin_path throws an exception in some test envs,
      # but is commonly defined in prod environments
      sdk_bin_path = config.Paths().sdk_bin_path
      if sdk_bin_path is None:
        log.critical(GKE_GCLOUD_AUTH_PLUGIN_NOT_FOUND)
      else:
        sdk_path_bin_name = os.path.join(sdk_bin_path, command)
        subprocess.run([sdk_path_bin_name, '--version'],
                       timeout=5,
                       check=False,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        command = sdk_path_bin_name  # update command if sdk_path_bin_name works
    except Exception:  # pylint: disable=broad-except
      log.critical(GKE_GCLOUD_AUTH_PLUGIN_NOT_FOUND)

  return command


def Context(name, cluster, user):
  """Generate and return a context kubeconfig object."""
  return {
      'name': name,
      'context': {
          'cluster': cluster,
          'user': user,
      },
  }


def EmptyKubeconfig():
  return {
      'apiVersion': 'v1',
      'contexts': [],
      'clusters': [],
      'current-context': '',
      'kind': 'Config',
      'preferences': {},
      'users': [],
  }
