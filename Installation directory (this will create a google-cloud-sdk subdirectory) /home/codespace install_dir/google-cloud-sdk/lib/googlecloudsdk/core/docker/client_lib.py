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
"""Utility library for working with docker clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import json
import os
import subprocess
import sys

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import semver

import six
from six.moves import urllib


DOCKER_NOT_FOUND_ERROR = 'Docker is not installed.'


class DockerError(exceptions.Error):
  """Base class for docker errors."""


class DockerConfigUpdateError(DockerError):
  """There was an error updating the docker configuration file."""


class InvalidDockerConfigError(DockerError):
  """The docker configuration file could not be read."""


def _GetUserHomeDir():
  if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
    # %HOME% has precedence over %USERPROFILE% for files.GetHomeDir().
    # The Docker config resides under %USERPROFILE% on Windows
    return encoding.Decode(os.path.expandvars('%USERPROFILE%'))
  else:
    return files.GetHomeDir()


def _GetNewConfigDirectory():
  # Return the value of $DOCKER_CONFIG, if it exists, otherwise ~/.docker
  # see https://github.com/moby/moby/blob/master/cli/config/configdir.go
  # NOTE: The preceding link is not owned by Google and cannot yet be updated to
  # address disrespectful term.
  docker_config = encoding.GetEncodedValue(os.environ, 'DOCKER_CONFIG')
  if docker_config is not None:
    return docker_config
  else:
    return os.path.join(_GetUserHomeDir(), '.docker')


# Other tools like the python docker library (used by gcloud app)
# also rely on Docker's authorization configuration (in addition
# to the docker CLI client)
# NOTE: Lazy for manipulation of HOME / mocking.
def GetDockerConfigPath(force_new=False):
  """Retrieve the path to Docker's configuration file, noting its format.

  Args:
    force_new: bool, whether to force usage of the new config file regardless
               of whether it exists (for testing).

  Returns:
    A tuple containing:
    -The path to Docker's configuration file, and
    -A boolean indicating whether it is in the new (1.7.0+) configuration format
  """
  # Starting in Docker 1.7.0, the Docker client moved where it writes
  # credentials to ~/.docker/config.json.  It is half backwards-compatible,
  # if the new file doesn't exist, it falls back on the old file.
  # if the new file exists, it IGNORES the old file.
  # This is a problem when a user has logged into another registry on 1.7.0
  # and then uses 'gcloud docker'.
  # This must remain compatible with: https://github.com/docker/docker-py
  new_path = os.path.join(_GetNewConfigDirectory(), 'config.json')
  if os.path.exists(new_path) or force_new:
    return new_path, True

  # Only one location will be probed to locate the new config.
  # This is consistent with the Docker client's behavior:
  # https://github.com/moby/moby/blob/master/cli/config/configdir.go
  # NOTE: The preceding link is not owned by Google and cannot yet be updated to
  # address disrespectful term.
  old_path = os.path.join(_GetUserHomeDir(), '.dockercfg')
  return old_path, False


def EnsureDocker(func):
  """Wraps a function that uses subprocess to invoke docker.

  Rewrites OS Exceptions when not installed.

  Args:
    func: A function that uses subprocess to invoke docker.

  Returns:
    The decorated function.

  Raises:
    DockerError: Docker cannot be run.
  """

  def DockerFunc(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except OSError as e:
      if e.errno == errno.ENOENT:
        raise DockerError(DOCKER_NOT_FOUND_ERROR)
      else:
        raise

  return DockerFunc


@EnsureDocker
def Execute(args):
  """Wraps an invocation of the docker client with the specified CLI arguments.

  Args:
    args: The list of command-line arguments to docker.

  Returns:
    The exit code from Docker.
  """
  return subprocess.call(
      ['docker'] + args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)


@EnsureDocker
def GetDockerProcess(docker_args, stdin_file, stdout_file, stderr_file):
  # Wraps the construction of a docker subprocess object with the specified
  # arguments and I/O files.
  return subprocess.Popen(
      ['docker'] + docker_args,
      stdin=stdin_file,
      stdout=stdout_file,
      stderr=stderr_file)


def GetDockerVersion():
  """Returns the installed Docker client version.

  Returns:
    The installed Docker client version.

  Raises:
    DockerError: Docker cannot be run or does not accept 'docker version
    --format '{{.Client.Version}}''.
  """
  docker_args = "version --format '{{.Client.Version}}'".split()

  docker_p = GetDockerProcess(
      docker_args,
      stdin_file=sys.stdin,
      stdout_file=subprocess.PIPE,
      stderr_file=subprocess.PIPE)

  # Wait for docker to finished executing and retrieve its stdout/stderr.
  stdoutdata, _ = docker_p.communicate()

  if docker_p.returncode != 0 or not stdoutdata:
    raise DockerError('could not retrieve Docker client version')

  # Remove ' from beginning and end of line.
  return semver.LooseVersion(stdoutdata.strip("'"))


def GetNormalizedURL(server):
  """Sanitize and normalize the server input."""
  parsed_url = urllib.parse.urlparse(server)
  # Work around the fact that Python 2.6 does not properly
  # look for :// and simply splits on colon, so something
  # like 'gcr.io:1234' returns the scheme 'gcr.io'.
  if '://' not in server:
    # Server doesn't have a scheme, set it to HTTPS.
    parsed_url = urllib.parse.urlparse('https://' + server)
    if parsed_url.hostname == 'localhost':
      # Now that it parses, if the hostname is localhost switch to HTTP.
      parsed_url = urllib.parse.urlparse('http://' + server)

  return parsed_url


def ReadConfigurationFile(path):
  """Retrieve the full contents of the Docker configuration file.

  Args:
    path: string, path to configuration file

  Returns:
    The full contents of the configuration file as parsed JSON dict.

  Raises:
    ValueError: path is not set.
    InvalidDockerConfigError: config file could not be read as JSON.
  """
  if not path:
    raise ValueError('Docker configuration file path is empty')

  # In many cases file might not exist even though Docker is installed,
  # so do not treat that as an error, just return empty contents.
  if not os.path.exists(path):
    return {}

  contents = files.ReadFileContents(path)
  # If the file is empty, return empty JSON.
  # This helps if someone 'touched' the file or manually
  # deleted the contents.
  if not contents or contents.isspace():
    return {}

  try:
    return json.loads(contents)
  except ValueError as err:
    raise InvalidDockerConfigError(
        ('Docker configuration file [{}] could not be read as JSON: '
         '{}').format(path, six.text_type(err)))
