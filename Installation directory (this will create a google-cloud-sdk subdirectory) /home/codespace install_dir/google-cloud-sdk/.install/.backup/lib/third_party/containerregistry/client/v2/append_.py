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
"""This package provides DockerImage for examining docker_build outputs."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import binascii
import json
import os

from containerregistry.client.v2 import docker_digest
from containerregistry.client.v2 import docker_image
from containerregistry.client.v2 import util

# _EMPTY_LAYER_TAR_ID is the sha256 of an empty tarball.
_EMPTY_LAYER_TAR_ID = 'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4'  # pylint: disable=line-too-long


class Layer(docker_image.DockerImage):
  """Appends a new layer on top of a base image.

  This augments a base docker image with new files from a gzipped tarball,
  adds environment variables and exposes a port.
  """

  def __init__(self, base, tar_gz,
               port, *envs):
    """Creates a new layer on top of a base with optional tar.gz, port or envs.

    Args:
      base: a base DockerImage for a new layer.
      tar_gz: an optional gzipped tarball passed as a string with filesystem
          changeset.
      port: an optional port to be exposed, passed as a string. For example:
          '8080/tcp'.
      *envs: environment variables passed as strings in the format:
          'ENV_ONE=val', 'ENV_TWO=val2'.
    """
    self._base = base

    unsigned_manifest, unused_signatures = util.DetachSignatures(
        self._base.manifest())
    manifest = json.loads(unsigned_manifest)
    v1_compat = json.loads(manifest['history'][0]['v1Compatibility'])

    if tar_gz:
      self._blob = tar_gz
      self._blob_sum = docker_digest.SHA256(self._blob)
      v1_compat['throwaway'] = False
    else:
      self._blob_sum = _EMPTY_LAYER_TAR_ID
      self._blob = b''
      v1_compat['throwaway'] = True

    manifest['fsLayers'].insert(0, {'blobSum': self._blob_sum})
    v1_compat['parent'] = v1_compat['id']
    v1_compat['id'] = binascii.hexlify(os.urandom(32)).decode('utf8')

    config = v1_compat.get('config', {}) or {}
    envs = list(envs)
    if envs:
      env_keys = [env.split('=')[0] for env in envs]
      old_envs = config.get('Env', []) or []
      old_envs = [env for env in old_envs if env.split('=')[0] not in env_keys]
      config['Env'] = old_envs + envs
    if port is not None:
      old_ports = config.get('ExposedPorts', {}) or {}
      old_ports[port] = {}
      config['ExposedPorts'] = old_ports
    v1_compat['config'] = config

    manifest['history'].insert(
        0, {'v1Compatibility': json.dumps(v1_compat, sort_keys=True)})
    self._manifest = util.Sign(json.dumps(manifest, sort_keys=True))

  def manifest(self):
    """Override."""
    return self._manifest

  def blob(self, digest):
    """Override."""
    if digest == self._blob_sum:
      return self._blob
    return self._base.blob(digest)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    """Override."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    return
