# Copyright 2017 Google Inc. All Rights Reserved.
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
"""This package manipulates Docker image metadata."""

from __future__ import absolute_import

from __future__ import print_function

from collections import namedtuple
import copy
import os
import six


_OverridesT = namedtuple('OverridesT', [
    'name', 'parent', 'size', 'entrypoint', 'cmd', 'env', 'labels', 'ports',
    'volumes', 'workdir', 'user'
])


class Overrides(_OverridesT):
  """Docker image layer metadata options."""

  def __new__(cls,
              name = None,
              parent = None,
              size = None,
              entrypoint = None,
              cmd = None,
              user = None,
              labels = None,
              env = None,
              ports = None,
              volumes = None,
              workdir = None):
    """Constructor."""
    return super(Overrides, cls).__new__(
        cls,
        name=name,
        parent=parent,
        size=size,
        entrypoint=entrypoint,
        cmd=cmd,
        user=user,
        labels=labels,
        env=env,
        ports=ports,
        volumes=volumes,
        workdir=workdir)


# NOT THREADSAFE
def _Resolve(value, environment):
  """Resolves environment variables embedded in the given value."""
  outer_env = os.environ
  try:
    os.environ = environment
    return os.path.expandvars(value)
  finally:
    os.environ = outer_env


# TODO(user): Use a typing.Generic?
def _DeepCopySkipNull(data):
  """Do a deep copy, skipping null entry."""
  if type(data) == type(dict()):  # pylint: disable=unidiomatic-typecheck
    return dict((_DeepCopySkipNull(k), _DeepCopySkipNull(v))
                for k, v in six.iteritems(data)
                if v is not None)
  return copy.deepcopy(data)


def _KeyValueToDict(pair):
  """Converts an iterable object of key=value pairs to dictionary."""
  d = dict()
  for kv in pair:
    (k, v) = kv.split('=', 1)
    d[k] = v
  return d


def _DictToKeyValue(d):
  return ['%s=%s' % (k, d[k]) for k in sorted(d.keys())]


def Override(data,
             options,
             docker_version = '1.5.0',
             architecture = 'amd64',
             operating_system = 'linux'):
  """Rewrite and return a copy of the input data according to options.

  Args:
    data: The dict of Docker image layer metadata we're copying and rewriting.
    options: The changes this layer makes to the overall image's metadata, which
             first appears in this layer's version of the metadata
    docker_version: The version of docker write in the metadata (default: 1.5.0)
    architecture: The architecture to write in the metadata (default: amd64)
    operating_system: The os to write in the metadata (default: linux)

  Returns:
    A deep copy of data, which has been updated to reflect the metadata
    additions of this layer.

  Raises:
    Exception: a required option was missing.
  """
  output = _DeepCopySkipNull(data)

  if not options.name:
    raise Exception('Missing required option: name')
  output['id'] = options.name

  if options.parent:
    output['parent'] = options.parent
  elif data:
    raise Exception(
        'Expected empty input object when parent is omitted, got: %s' % data)

  if options.size:
    output['Size'] = options.size
  elif 'Size' in output:
    del output['Size']

  if 'config' not in output:
    output['config'] = {}

  if options.entrypoint:
    output['config']['Entrypoint'] = options.entrypoint
  if options.cmd:
    output['config']['Cmd'] = options.cmd
  if options.user:
    output['config']['User'] = options.user

  output['docker_version'] = docker_version
  output['architecture'] = architecture
  output['os'] = operating_system

  if options.env:
    # Build a dictionary of existing environment variables (used by _Resolve).
    environ_dict = _KeyValueToDict(output['config'].get('Env', []))
    # Merge in new environment variables, resolving references.
    for k, v in six.iteritems(options.env):
      # _Resolve handles scenarios like "PATH=$PATH:...".
      environ_dict[k] = _Resolve(v, environ_dict)
    output['config']['Env'] = _DictToKeyValue(environ_dict)

  if options.labels:
    label_dict = _KeyValueToDict(output['config'].get('Label', []))
    for k, v in six.iteritems(options.labels):
      label_dict[k] = v
    output['config']['Label'] = _DictToKeyValue(label_dict)

  if options.ports:
    if 'ExposedPorts' not in output['config']:
      output['config']['ExposedPorts'] = {}
    for p in options.ports:
      if '/' in p:
        # The port spec has the form 80/tcp, 1234/udp
        # so we simply use it as the key.
        output['config']['ExposedPorts'][p] = {}
      else:
        # Assume tcp for naked ports.
        output['config']['ExposedPorts'][p + '/tcp'] = {}

  if options.volumes:
    if 'Volumes' not in output['config']:
      output['config']['Volumes'] = {}
    for p in options.volumes:
      output['config']['Volumes'][p] = {}

  if options.workdir:
    output['config']['WorkingDir'] = options.workdir

  # TODO(user): comment, created, container_config

  # container_config contains information about the container
  # that was used to create this layer, so it shouldn't
  # propagate from the parent to child.  This is where we would
  # annotate information that can be extract by tools like Blubber
  # or Quay.io's UI to gain insight into the source that generated
  # the layer.  A Dockerfile might produce something like:
  #   # (nop) /bin/sh -c "apt-get update"
  # We might consider encoding the fully-qualified bazel build target:
  #  //tools/build_defs/docker:image
  # However, we should be sensitive to leaking data through this field.
  if 'container_config' in output:
    del output['container_config']

  return output
