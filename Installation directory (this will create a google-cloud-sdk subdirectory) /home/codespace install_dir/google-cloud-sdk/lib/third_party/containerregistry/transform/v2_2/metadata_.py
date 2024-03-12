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
"""This package manipulates v2.2 image configuration metadata."""

from __future__ import absolute_import

from __future__ import print_function

from collections import namedtuple
import copy
import hashlib
import os

import six


_OverridesT = namedtuple('OverridesT', [
    'layers', 'entrypoint', 'cmd', 'env', 'labels', 'ports', 'volumes',
    'workdir', 'user', 'author', 'created_by', 'creation_time'
])

# Unix epoch 0, representable in 32 bits.
_DEFAULT_TIMESTAMP = '1970-01-01T00:00:00Z'

_EMPTY_LAYER = hashlib.sha256(b'').hexdigest()


class Overrides(_OverridesT):
  """Docker image configuration options."""

  def __new__(cls,
              layers = None,
              entrypoint = None,
              cmd = None,
              user = None,
              labels = None,
              env = None,
              ports = None,
              volumes = None,
              workdir = None,
              author = None,
              created_by = None,
              creation_time = None):
    """Constructor."""
    return super(Overrides, cls).__new__(
        cls,
        layers=layers,
        entrypoint=entrypoint,
        cmd=cmd,
        user=user,
        labels=labels,
        env=env,
        ports=ports,
        volumes=volumes,
        workdir=workdir,
        author=author,
        created_by=created_by,
        creation_time=creation_time)

  def Override(self,
               layers = None,
               entrypoint = None,
               cmd = None,
               user = None,
               labels = None,
               env = None,
               ports = None,
               volumes = None,
               workdir = None,
               author = None,
               created_by = None,
               creation_time = None):
    return Overrides(
        layers=layers or self.layers,
        entrypoint=entrypoint or self.entrypoint,
        cmd=cmd or self.cmd,
        user=user or self.user,
        labels=labels or self.labels,
        env=env or self.env,
        ports=ports or self.ports,
        volumes=volumes or self.volumes,
        workdir=workdir or self.workdir,
        author=author or self.author,
        created_by=created_by or self.created_by,
        creation_time=creation_time or self.creation_time)


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
  if isinstance(data, dict):
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
             architecture = 'amd64',
             operating_system = 'linux'):
  """Create an image config possibly based on an existing one.

  Args:
    data: A dict of Docker image config to base on top of.
    options: Options specific to this image which will be merged with any
             existing data
    architecture: The architecture to write in the metadata (default: amd64)
    operating_system: The os to write in the metadata (default: linux)

  Returns:
    Image config for the new image
  """
  defaults = _DeepCopySkipNull(data)

  # dont propagate non-spec keys
  output = dict()
  output['created'] = options.creation_time or _DEFAULT_TIMESTAMP
  output['author'] = options.author or 'Unknown'
  output['architecture'] = architecture
  output['os'] = operating_system

  if 'os.version' in defaults:
    output['os.version'] = defaults['os.version']

  output['config'] = defaults.get('config', {})

  # pytype: disable=attribute-error,unsupported-operands
  if options.entrypoint:
    output['config']['Entrypoint'] = options.entrypoint
  if options.cmd:
    output['config']['Cmd'] = options.cmd
  if options.user:
    output['config']['User'] = options.user

  if options.env:
    # Build a dictionary of existing environment variables (used by _Resolve).
    environ_dict = _KeyValueToDict(output['config'].get('Env', []))
    # Merge in new environment variables, resolving references.
    for k, v in six.iteritems(options.env):
      # Resolve handles scenarios like "PATH=$PATH:...".
      environ_dict[k] = _Resolve(v, environ_dict)
    output['config']['Env'] = _DictToKeyValue(environ_dict)

  # TODO(user) Label is currently docker specific
  if options.labels:
    label_dict = output['config'].get('Labels', {})
    for k, v in six.iteritems(options.labels):
      label_dict[k] = v
    output['config']['Labels'] = label_dict

  if options.ports:
    if 'ExposedPorts' not in output['config']:
      output['config']['ExposedPorts'] = {}
    for p in options.ports:
      if '/' in p:
        # The port spec has the form 80/tcp, 1234/udp
        # so we simply use it as the key.
        output['config']['ExposedPorts'][p] = {}
      else:
        # Assume tcp
        output['config']['ExposedPorts'][p + '/tcp'] = {}

  if options.volumes:
    if 'Volumes' not in output['config']:
      output['config']['Volumes'] = {}
    for p in options.volumes:
      output['config']['Volumes'][p] = {}

  if options.workdir:
    output['config']['WorkingDir'] = options.workdir
  # pytype: enable=attribute-error,unsupported-operands

  # diff_ids are ordered from bottom-most to top-most
  diff_ids = defaults.get('rootfs', {}).get('diff_ids', [])
  if options.layers:
    layers = options.layers
    diff_ids += ['sha256:%s' % l for l in layers if l != _EMPTY_LAYER]
    output['rootfs'] = {
        'type': 'layers',
        'diff_ids': diff_ids,
    }

    # The length of history is expected to match the length of diff_ids.
    history = defaults.get('history', [])
    for l in layers:
      cfg = {
          'created': options.creation_time or _DEFAULT_TIMESTAMP,
          'created_by': options.created_by or 'Unknown',
          'author': options.author or 'Unknown'
      }
      if l == _EMPTY_LAYER:
        cfg['empty_layer'] = True
      history.insert(0, cfg)
    output['history'] = history

  return output
