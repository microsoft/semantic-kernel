# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Utility library for configuring access to the Google Container Registry.

Sets docker up to authenticate with the Google Container Registry using the
active gcloud credential.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import os
import subprocess
import sys

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.docker import client_lib
from googlecloudsdk.core.docker import constants
from googlecloudsdk.core.util import files
import six


_USERNAME = 'gclouddockertoken'
_EMAIL = 'not@val.id'
_CREDENTIAL_STORE_KEY = 'credsStore'


class UnsupportedRegistryError(client_lib.DockerError):
  """Indicates an attempt to use an unsupported registry."""

  def __init__(self, image_url):
    self.image_url = image_url

  def __str__(self):
    return ('{0} is not in a supported registry.  Supported registries are '
            '{1}'.format(self.image_url, constants.ALL_SUPPORTED_REGISTRIES))


def DockerLogin(server, username, access_token):
  """Register the username / token for the given server on Docker's keyring."""

  # Sanitize and normalize the server input.
  parsed_url = client_lib.GetNormalizedURL(server)

  server = parsed_url.geturl()

  # 'docker login' must be used due to the change introduced in
  # https://github.com/docker/docker/pull/20107 .
  docker_args = ['login']
  docker_args.append('--username=' + username)
  docker_args.append('--password=' + access_token)
  docker_args.append(server)  # The auth endpoint must be the last argument.

  docker_p = client_lib.GetDockerProcess(
      docker_args,
      stdin_file=sys.stdin,
      stdout_file=subprocess.PIPE,
      stderr_file=subprocess.PIPE)

  # Wait for docker to finished executing and retrieve its stdout/stderr.
  stdoutdata, stderrdata = docker_p.communicate()

  if docker_p.returncode == 0:
    # If the login was successful, print only unexpected info.
    _SurfaceUnexpectedInfo(stdoutdata, stderrdata)
  else:
    # If the login failed, print everything.
    log.error('Docker CLI operation failed:')
    log.out.Print(stdoutdata)
    log.status.Print(stderrdata)
    raise client_lib.DockerError('Docker login failed.')


def _SurfaceUnexpectedInfo(stdoutdata, stderrdata):
  """Reads docker's output and surfaces unexpected lines.

  Docker's CLI has a certain amount of chattiness, even on successes.

  Args:
    stdoutdata: The raw data output from the pipe given to Popen as stdout.
    stderrdata: The raw data output from the pipe given to Popen as stderr.
  """

  # Split the outputs by lines.
  stdout = [s.strip() for s in stdoutdata.splitlines()]
  stderr = [s.strip() for s in stderrdata.splitlines()]

  for line in stdout:
    # Swallow 'Login Succeeded' and 'saved in,' surface any other std output.
    if (line != 'Login Succeeded') and (
        'login credentials saved in' not in line):
      line = '%s%s' % (line, os.linesep)
      log.out.Print(line)  # log.out => stdout

  for line in stderr:
    if not _IsExpectedErrorLine(line):
      line = '%s%s' % (line, os.linesep)
      log.status.Print(line)  # log.status => stderr


def _CredentialStoreConfigured():
  """Returns True if a credential store is specified in the docker config.

  Returns:
    True if a credential store is specified in the docker config.
    False if the config file does not exist or does not contain a
    'credsStore' key.
  """
  try:
    # Not Using DockerConfigInfo here to be backward compatiable with
    # UpdateDockerCredentials which should still work if Docker is not installed
    path, is_new_format = client_lib.GetDockerConfigPath()
    contents = client_lib.ReadConfigurationFile(path)
    if is_new_format:
      return _CREDENTIAL_STORE_KEY in contents
    else:
      # The old format is for Docker <1.7.0.
      # Older Docker clients (<1.11.0) don't support credential helpers.
      return False
  except IOError:
    # Config file doesn't exist.
    return False


def ReadDockerAuthConfig():
  """Retrieve the contents of the Docker authorization entry.

  NOTE: This is public only to facilitate testing.

  Returns:
    The map of authorizations used by docker.
  """
  # Not using DockerConfigInfo here to be backward compatible with
  # UpdateDockerCredentials which should still work if Docker is not installed
  path, new_format = client_lib.GetDockerConfigPath()
  structure = client_lib.ReadConfigurationFile(path)
  if new_format:
    return structure['auths'] if 'auths' in structure else {}
  else:
    return structure


def WriteDockerAuthConfig(structure):
  """Write out a complete set of Docker authorization entries.

  This is public only to facilitate testing.

  Args:
    structure: The dict of authorization mappings to write to the
               Docker configuration file.
  """
  # Not using DockerConfigInfo here to be backward compatible with
  # UpdateDockerCredentials which should still work if Docker is not installed
  path, is_new_format = client_lib.GetDockerConfigPath()
  contents = client_lib.ReadConfigurationFile(path)
  if is_new_format:
    full_cfg = contents
    full_cfg['auths'] = structure
    file_contents = json.dumps(full_cfg, indent=2)
  else:
    file_contents = json.dumps(structure, indent=2)
  files.WriteFileAtomically(path, file_contents)


def UpdateDockerCredentials(server, refresh=True):
  """Updates the docker config to have fresh credentials.

  This reads the current contents of Docker's keyring, and extends it with
  a fresh entry for the provided 'server', based on the active gcloud
  credential.  If a credential exists for 'server' this replaces it.

  Args:
    server: The hostname of the registry for which we're freshening
       the credential.
    refresh: Whether to force a token refresh on the active credential.

  Raises:
    core.credentials.exceptions.Error: There was an error loading the
      credentials.
  """

  if refresh:
    access_token = store.GetFreshAccessToken()
  else:
    access_token = store.GetAccessToken()

  if not access_token:
    raise exceptions.Error(
        'No access token could be obtained from the current credentials.')

  if _CredentialStoreConfigured():
    try:
      # Update the credentials stored by docker, passing the sentinel username
      # and access token.
      DockerLogin(server, _USERNAME, access_token)
    except client_lib.DockerError as e:
      # Only catch docker-not-found error
      if six.text_type(e) != client_lib.DOCKER_NOT_FOUND_ERROR:
        raise

      # Fall back to the previous manual .dockercfg manipulation
      # in order to support gcloud app's docker-binaryless use case.
      _UpdateDockerConfig(server, _USERNAME, access_token)
      log.warning(
          "'docker' was not discovered on the path. Credentials have been "
          'stored, but are not guaranteed to work with the Docker client '
          ' if an external credential store is configured.')
  else:
    _UpdateDockerConfig(server, _USERNAME, access_token)


def _UpdateDockerConfig(server, username, access_token):
  """Register the username / token for the given server on Docker's keyring."""

  # NOTE: using "docker login" doesn't work as they're quite strict on what
  # is allowed in username/password.
  try:
    dockercfg_contents = ReadDockerAuthConfig()
  except (IOError, client_lib.InvalidDockerConfigError):
    # If the file doesn't exist, start with an empty map.
    dockercfg_contents = {}

  # Add the entry for our server.
  auth = username + ':' + access_token
  auth = base64.b64encode(auth.encode('ascii')).decode('ascii')

  # Sanitize and normalize the server input.
  parsed_url = client_lib.GetNormalizedURL(server)

  server = parsed_url.geturl()
  server_unqualified = parsed_url.hostname

  # Clear out any unqualified stale entry for this server
  if server_unqualified in dockercfg_contents:
    del dockercfg_contents[server_unqualified]

  dockercfg_contents[server] = {'auth': auth, 'email': _EMAIL}

  WriteDockerAuthConfig(dockercfg_contents)


def _IsExpectedErrorLine(line):
  """Returns whether or not the given line was expected from the Docker client.

  Args:
    line: The line received in stderr from Docker
  Returns:
    True if the line was expected, False otherwise.
  """
  expected_line_substrs = [
      # --email is deprecated
      '--email',
      # login success
      'login credentials saved in',
      # Use stdin for passwords
      'WARNING! Using --password via the CLI is insecure. Use --password-stdin.'
  ]
  for expected_line_substr in expected_line_substrs:
    if expected_line_substr in line:
      return True
  return False
