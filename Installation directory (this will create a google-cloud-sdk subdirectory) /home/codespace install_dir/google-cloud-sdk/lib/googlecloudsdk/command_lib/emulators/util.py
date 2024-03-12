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
"""Utility functions for gcloud emulators datastore group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import contextlib
import os
import random
import re
import socket
import subprocess
import tempfile

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
import portpicker
import six


_IPV6_RE = re.compile(r'\[(.*)\]:(\d*)')


class NoCloudSDKError(exceptions.Error):
  """The module was unable to find Cloud SDK."""

  def __init__(self):
    super(NoCloudSDKError, self).__init__(
        'Unable to find a Cloud SDK installation.')


class NoEnvYamlError(exceptions.Error):
  """Unable to find a env.yaml file."""

  def __init__(self, data_dir):
    super(NoEnvYamlError, self).__init__(
        'Unable to find env.yaml in the data_dir [{0}]. Please ensure you have'
        ' started the appropriate emulator.'.format(data_dir))


class MissingProxyError(exceptions.Error):
  pass


class NoEmulatorError(exceptions.Error):
  pass


class InvalidHostError(exceptions.Error):
  """The configured host:port is invalid."""

  def __init__(self):
    super(InvalidHostError, self).__init__(
        'Emulator host-port must take the form ADDRESS:PORT where ADDRESS'
        ' is a hostname, IPv4 or IPv6 address.')


def EnsureComponentIsInstalled(component_id, for_text):
  """Ensures that the specified component is installed.

  Args:
    component_id: str, the name of the component
    for_text: str, the text explaining what the component is necessary for

  Raises:
    NoCloudSDKError: If a Cloud SDK installation is not found.
  """
  msg = ('You need the [{0}] component to use the {1}.'
         .format(component_id, for_text))
  try:
    update_manager.UpdateManager.EnsureInstalledAndRestart([component_id],
                                                           msg=msg)
  except local_state.InvalidSDKRootError:
    raise NoCloudSDKError()


def GetCloudSDKRoot():
  """Gets the directory of the root of the Cloud SDK, error if it doesn't exist.

  Raises:
    NoCloudSDKError: If there is no SDK root.

  Returns:
    str, The path to the root of the Cloud SDK.
  """
  sdk_root = config.Paths().sdk_root
  if not sdk_root:
    raise NoCloudSDKError()
  log.debug('Found Cloud SDK root: %s', sdk_root)
  return sdk_root


def WriteEnvYaml(env, output_dir):
  """Writes the given environment values into the output_dir/env.yaml file.

  Args:
    env: {str: str}, Dictonary of environment values.
    output_dir: str, Path of directory to which env.yaml file should be written.
  """
  env_file_path = os.path.join(output_dir, 'env.yaml')
  with files.FileWriter(env_file_path) as env_file:
    resource_printer.Print([env], print_format='yaml', out=env_file)


def ReadEnvYaml(output_dir):
  """Reads and returns the environment values in output_dir/env.yaml file.

  Args:
    output_dir: str, Path of directory containing the env.yaml to be read.

  Returns:
    env: {str: str}
  """
  env_file_path = os.path.join(output_dir, 'env.yaml')
  try:
    with files.FileReader(env_file_path) as f:
      return yaml.load(f)
  except files.MissingFileError:
    raise NoEnvYamlError(output_dir)


def PrintEnvExport(env):
  """Print OS specific export commands for the given environment values.

  Args:
    env: {str: str}, Dictonary of environment values.
  """
  current_os = platforms.OperatingSystem.Current()
  export_command = 'export'
  if current_os is platforms.OperatingSystem.WINDOWS:
    export_command = 'set'
  for var, value in six.iteritems(env):
    if ' ' in value:
      value = '"{value}"'.format(value=value)
    log.Print('{export_command} {var}={value}'.format(
        export_command=export_command,
        var=var,
        value=value))


def PrintEnvUnset(env):
  """Print OS specific unset commands for the given environment variables.

  Args:
    env: {str: str}, Dictionary of environment values, the value is ignored.
  """
  current_os = platforms.OperatingSystem.Current()
  export_command = 'unset {var}'
  if current_os is platforms.OperatingSystem.WINDOWS:
    export_command = 'set {var}='
  for var in six.iterkeys(env):
    log.Print(export_command.format(var=var))


def GetDataDir(prefix):
  """If present, returns the configured data dir, else returns the default.

  Args:
    prefix: pubsub, datastore, bigtable, etc. The prefix for the *_data_dir
    property of the emulators section.

  Returns:
    str, The configured or default data_dir path.
  """
  configured = _GetEmulatorProperty(prefix, 'data_dir')
  if configured: return configured

  config_root = config.Paths().global_config_dir
  default_data_dir = os.path.join(config_root, 'emulators', prefix)
  files.MakeDir(default_data_dir)
  return default_data_dir


def GetHostPort(prefix):
  """If present, returns the configured host port, else returns the default.

  Args:
    prefix: str, The prefix for the *-emulator property group to look up.

  Raises:
    InvalidHostError: If configured host-port is not of the form
    ADDRESS:PORT.

  Returns:
    str, Configured or default host_port if present, else an unused local port.
  """
  default_host = '[::1]' if socket.has_ipv6 else 'localhost'

  # Can't use portpicker here, as it only finds free ports on localhost.
  arbitrary_host_port = '{host}:{port}'.format(
      host=default_host, port=random.randint(8000, 8999))
  configured = _GetEmulatorProperty(prefix, 'host_port') or arbitrary_host_port
  try:
    host, port = _ParseHostPort(configured)
    protocol = socket.AF_INET6 if _IPV6_RE.match(configured) else socket.AF_INET
    sock = socket.socket(protocol, socket.SOCK_STREAM)
    port = int(port)
  except ValueError:
    raise InvalidHostError()

  if sock.connect_ex((host, port)) != 0:
    return configured

  return arbitrary_host_port


def _ParseHostPort(hostport):
  if _IPV6_RE.match(hostport):
    return _IPV6_RE.match(hostport).groups()
  else:
    return hostport.split(':')


def _GetEmulatorProperty(prefix, prop_name):
  """Returns the value of the given property in the given emulator group.

  Args:
    prefix: str, The prefix for the *_emulator property group to look up.
    prop_name: str, The name of the property to look up.

  Returns:
    str, The the value of the given property in the specified emulator group.
  """
  property_group = 'emulator'
  full_name = '{}_{}'.format(prefix, prop_name)
  for section in properties.VALUES:
    if section.name == property_group and section.HasProperty(full_name):
      return section.Property(full_name).Get()
  return None


@contextlib.contextmanager
def Exec(args, log_file=None):
  """Starts subprocess with given args and ensures its termination upon exit.

  This starts a subprocess with the given args. The stdout and stderr of the
  subprocess are piped. Note that this is a context manager, to ensure that
  processes (and references to them) are not leaked.

  Args:
    args: [str], The arguments to execute. The first argument is the command.
    log_file: optional file argument to reroute process's output. If given,
      will be closed when the file is terminated.

  Yields:
    process, The process handle of the subprocess that has been started.
  """
  reroute_stdout = log_file or subprocess.PIPE
  if not platforms.OperatingSystem.IsWindows():
    # Check if pid is session leader.
    if os.getsid(0) != os.getpid():
      os.setpgid(0, 0)
  process = subprocess.Popen(args,
                             stdout=reroute_stdout,
                             stderr=subprocess.STDOUT)
  try:
    yield process
  finally:
    if process.poll() is None:
      process.terminate()
      process.wait()


def PrefixOutput(process, prefix):
  """Prepends the given prefix to each line of the given process's output.

  Args:
    process: process, The handle to the process whose output should be prefixed
    prefix: str, The prefix to be prepended to the process's output.
  """
  output_line = process.stdout.readline()
  while output_line:
    log.status.Print('[{0}] {1}'.format(prefix,
                                        encoding.Decode(output_line.rstrip())))
    log.status.flush()
    output_line = process.stdout.readline()


def BuildArgsList(args):
  """Converts an argparse.Namespace to a list of arg strings."""
  args_list = []
  if args.host_port:
    if _IPV6_RE.match(args.host_port.host):
      host = '[{}]'.format(args.host_port.host)
    else:
      host = args.host_port.host

    if args.host_port.host is not None:
      args_list.append('--host={0}'.format(host))
    if args.host_port.port is not None:
      args_list.append('--port={0}'.format(args.host_port.port))
  return args_list


def GetEmulatorRoot(emulator):
  emulator_dir = os.path.join(GetCloudSDKRoot(),
                              'platform', '{0}-emulator'.format(emulator))
  if not os.path.isdir(emulator_dir):
    raise NoEmulatorError('No {0} directory found.'.format(emulator))
  return emulator_dir


def GetEmulatorProxyPath():
  """Returns path to the emulator reverse proxy."""
  path = os.path.join(GetCloudSDKRoot(), 'platform', 'emulator-reverse-proxy')
  if not os.path.isdir(path):
    # We shouldn't get here because the emulators package should ensure that
    # this component installed. That's computers for you, though!
    # TODO(b/36654459) We should potentially allow the user to specify a
    # location via a property
    raise MissingProxyError(
        'emulator-reverse-proxy component must be installed. try running '
        '`gcloud components install emulator-reverse-proxy`')
  return path


class AttrDict(object):
  """Allows for a wrapped map to be indexed via attributes instead of keys.

  Example:
  m = {'a':'b', 'c':{'d':'e', 'f':'g'}}
  a = AttrDict(m)
  m['c']['d'] == a.c.d
  """

  def __init__(self, _dict, recurse=True):
    """Initializes attributes dictionary.

    Args:
      _dict: dict, the map to convert into an attribute dictionary
      recurse: bool, if True then any nested maps will also be treated as
               attribute dictionaries
    """
    if recurse:
      dict_copy = {}
      for key, value in six.iteritems(_dict):
        toset = value
        if isinstance(value, dict):
          toset = AttrDict(value, recurse)
        dict_copy[key] = toset
      self._dict = dict_copy
    else:
      self._dict = _dict
    self._recurse = recurse

  def __getattr__(self, attr):
    return self._dict[attr]

  def __setattr__(self, attr, value):
    if attr in set(['_dict', '_recurse']):
      super(AttrDict, self).__setattr__(attr, value)
    else:
      self._dict[attr] = value


class Emulator(six.with_metaclass(abc.ABCMeta)):
  """This organizes the information to expose an emulator."""

  # TODO(b/35871640) Right now, there is no error handling contract with the
  #   subclasses. This means that if the subclass process fails, there is no
  #  way to detect that, surface that, etc. We could implement a contract as
  #  well as liveness checks etc to ensure that we detect if a process has
  #  failed and respond gracefully.
  @abc.abstractmethod
  def Start(self, port):
    """Starts the emulator process on the given port.

    Args:
      port: int, port number for emulator to bind to

    Returns:
      subprocess.Popen, the emulator process
    """
    raise NotImplementedError()

  @property
  @abc.abstractproperty
  def prefixes(self):
    """Returns the grpc route prefixes to route to this service.

    Returns:
      list(str), list of prefixes.
    """
    raise NotImplementedError()

  @property
  @abc.abstractproperty
  def service_name(self):
    """Returns the service name this emulator corresponds to.

    Note that it is assume that the production API this service is emulating
    exists at <name>.googleapis.com

    Returns:
      str, the service name
    """
    raise NotImplementedError()

  @property
  @abc.abstractproperty
  def emulator_title(self):
    """Returns title of the emulator.

    This is just for nice rendering in the cloud sdk.

    Returns:
      str, the emulator title
    """
    raise NotImplementedError()

  @property
  @abc.abstractproperty
  def emulator_component(self):
    """Returns cloud sdk component to install.

    Returns:
      str, cloud sdk component name
    """
    raise NotImplementedError()

  def _GetLogNo(self):
    """Returns the OS-level handle to log file.

    This handle is the same as would be returned by os.open(). This is what the
    subprocess interface expects. Note that the caller needs to make sure to
    close this to avoid leaking file descriptors.

    Returns:
      int, OS-level handle to log file
    """
    log_file_no, log_file = tempfile.mkstemp()
    log.status.Print('Logging {0} to: {1}'.format(self.service_name, log_file))
    return log_file_no


class EmulatorArgumentsError(exceptions.Error):
  """Generic error for invalid arguments."""
  pass


_DEFAULT_PORT = 45763


def DefaultPortIfAvailable():
  """Returns default port if available.

  Raises:
    EmulatorArgumentsError: if port is not available.

  Returns:
    int, default port
  """
  if portpicker.is_port_free(_DEFAULT_PORT):
    return _DEFAULT_PORT
  else:
    raise EmulatorArgumentsError(
        'Default emulator port [{}] is already in use'.format(_DEFAULT_PORT))
