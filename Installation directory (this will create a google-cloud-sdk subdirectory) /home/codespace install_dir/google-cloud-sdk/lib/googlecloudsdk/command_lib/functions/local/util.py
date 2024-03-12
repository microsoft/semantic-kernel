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
"""Utilities used by gcloud functions local development."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re
import textwrap
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.util import files

import six

_INSTALLATION_GUIDE = textwrap.dedent("""\
    You must install Docker and Pack to run this command.
    To install Docker and Pack, please follow this guide:
    <INSERT_LINK_HERE>""")
_DOCKER = files.FindExecutableOnPath('docker')
_PACK = files.FindExecutableOnPath('pack')
_APPENGINE_BUILDER = 'gcr.io/gae-runtimes/buildpacks/google-gae-{}/{}/builder'
_V1_BUILDER = 'gcr.io/buildpacks/builder:v1'
_GOOGLE_22_BUILDER = 'gcr.io/buildpacks/builder:google-22'
_RUNTIME_MINVERSION_UBUNTU_22 = {'python': 310, 'nodejs': 18, 'go': 116,
                                 'java': 17, 'php': 82, 'ruby': 32,
                                 'dotnet': 6}


class MissingExecutablesException(core_exceptions.Error):
  """Executables for local development are not found."""


class ContainerNotFoundException(core_exceptions.Error):
  """Docker container is not found."""


class DockerExecutionException(core_exceptions.Error):
  """Docker executable exited with non-zero code."""


class PackExecutionException(core_exceptions.Error):
  """Pack executable exited with non-zero code."""


def ValidateDependencies():
  if _DOCKER is None or _PACK is None:
    raise MissingExecutablesException(_INSTALLATION_GUIDE)


def RunPack(name, builder, runtime, entry_point, path, build_env_vars):
  """Runs Pack Build with the command built from arguments of the command parser.

  Args:
    name: Name of the image build.
    builder: Name of the builder by the flag.
    runtime: Runtime specified by flag.
    entry_point: Entry point of the function specified by flag.
    path: Source of the zip file.
    build_env_vars: Build environment variables.
  Raises:
    PackExecutionException: if the exit code of the execution is non-zero.
  """
  pack_cmd = [_PACK, 'build', '--builder']

  # Always use language-specific builder when builder not provided.
  if not builder:
    [language, version] = re.findall(r'(\D+|\d+)', runtime)
    if int(version) >= _RUNTIME_MINVERSION_UBUNTU_22[language]:
      builder = (_GOOGLE_22_BUILDER if language == 'dotnet'
                 else _APPENGINE_BUILDER.format(22, language))
    else:
      builder = (_V1_BUILDER if language == 'dotnet'
                 else _APPENGINE_BUILDER.format(18, language))
  pack_cmd.append(builder)

  if build_env_vars:
    _AddEnvVars(pack_cmd, build_env_vars)

  pack_cmd.extend(['--env', 'GOOGLE_FUNCTION_TARGET=' + entry_point])
  pack_cmd.extend(['--path', path])
  pack_cmd.extend(['-q', name])
  status = execution_utils.Exec(pack_cmd, no_exit=True)
  if status:
    raise PackExecutionException(
        status, 'Pack failed to build the container image.')


def RunDockerContainer(name, port, env_vars, labels):
  """Runs the Docker container (detached mode) with specified port and name.

  If the name already exists, it will be removed.

  Args:
    name: The name of the container to run.
    port: The port for the container to run on.
    env_vars: The container environment variables.
    labels: Docker labels to store flags and environment variables.

  Raises:
    DockerExecutionException: if the exit code of the execution is non-zero.
  """
  if ContainerExists(name):
    RemoveDockerContainer(name)
  docker_cmd = [_DOCKER, 'run', '-d']
  docker_cmd.extend(['-p', six.text_type(port) + ':8080'])
  if env_vars:
    _AddEnvVars(docker_cmd, env_vars)
  for k, v in labels.items():
    docker_cmd.extend(['--label', '{}={}'.format(k, json.dumps(v))])
  docker_cmd.extend(['--name', name, name])
  status = execution_utils.Exec(docker_cmd, no_exit=True)
  if status:
    raise DockerExecutionException(
        status, 'Docker failed to run container ' + name)


def RemoveDockerContainer(name):
  """Removes the Docker container with specified name.

  Args:
    name: The name of the Docker container to delete.

  Raises:
    DockerExecutionException: if the exit code of the execution is non-zero.
  """
  delete_cmd = [_DOCKER, 'rm', '-f', name]
  status = execution_utils.Exec(delete_cmd, no_exit=True)
  if status:
    raise DockerExecutionException(
        status, 'Docker failed to execute: failed to remove container ' + name)


def ContainerExists(name):
  """Returns True if the Docker container with specified name exists.

  Args:
    name: The name of the Docker container.

  Returns:
    bool: True if the container exists, False otherwise.

  Raises:
    DockerExecutionException: if the exit code of the execution is non-zero.
  """
  list_cmd = [_DOCKER, 'ps', '-q', '-f', 'name=' + name]
  out = []
  capture_out = lambda stdout: out.append(stdout.strip())
  status = execution_utils.Exec(list_cmd, out_func=capture_out, no_exit=True)
  if status:
    raise DockerExecutionException(
        status, 'Docker failed to execute: failed to list container ' + name)
  return bool(out[0])


def FindContainerPort(name):
  """Returns the port of the Docker container with specified name.

  Args:
    name: The name of the Docker container.

  Returns:
    str: The port number of the Docker container.

  Raises:
    DockerExecutionException: if the exit code of the execution is non-zero
    or if the port of the container does not exist.
  """
  mapping = """{{range $p, $conf := .NetworkSettings.Ports}}\
      {{(index $conf 0).HostPort}}{{end}}"""
  find_port = [_DOCKER, 'inspect', '--format=' + mapping, name]
  out = []
  capture_out = lambda stdout: out.append(stdout.strip())
  status = execution_utils.Exec(find_port, out_func=capture_out, no_exit=True)
  if status:
    raise DockerExecutionException(
        status, 'Docker failed to execute: failed to find port for ' + name)
  return out[0]


def GetDockerContainerLabels(name):
  """Returns the labels of the Docker container with specified name.

  Args:
    name: The name of the Docker container.

  Returns:
    dict: The labels for the docker container in json format.

  Raises:
    DockerExecutionException: if the exit code of the execution is non-zero
    or if the port of the container does not exist.
  """
  if not ContainerExists(name):
    return {}
  find_labels = [_DOCKER, 'inspect', '--format={{json .Config.Labels}}', name]
  out = []
  capture_out = lambda stdout: out.append(stdout.strip())
  status = execution_utils.Exec(find_labels, out_func=capture_out, no_exit=True)
  if status:
    raise DockerExecutionException(
        status, 'Docker failed to execute: failed to labels for ' + name)
  return json.loads(out[0])


def _AddEnvVars(cmd_args, env_vars):
  for key, value in env_vars.items():
    cmd_args.extend(['--env', key + '=' + value])
