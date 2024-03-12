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
"""This package provides tools for appending layers to docker images."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import json

from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_digest
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from containerregistry.transform.v2_2 import metadata

# _EMPTY_LAYER_TAR_ID is the sha256 of an empty tarball.
_EMPTY_LAYER_TAR_ID = 'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4'


class Layer(docker_image.DockerImage):
  """Appends a new layer on top of a base image.

  This augments a base docker image with new files from a gzipped tarball,
  adds environment variables and exposes a port.
  """

  def __init__(self,
               base,
               tar_gz,
               diff_id = None,
               overrides = None):
    """Creates a new layer on top of a base with optional tar.gz.

    Args:
      base: a base DockerImage for a new layer.
      tar_gz: an optional gzipped tarball passed as a bytes with filesystem
          changeset.
      diff_id: an optional string containing the digest of the
          uncompressed tar_gz.
      overrides: an optional metadata.Overrides object of properties to override
          on the base image.
    """
    self._base = base
    manifest = json.loads(self._base.manifest())
    config_file = json.loads(self._base.config_file())

    overrides = overrides or metadata.Overrides()
    overrides = overrides.Override(created_by=docker_name.USER_AGENT)

    if tar_gz:
      self._blob = tar_gz
      self._blob_sum = docker_digest.SHA256(self._blob)
      manifest['layers'].append({
          'digest': self._blob_sum,
          'mediaType': docker_http.LAYER_MIME,
          'size': len(self._blob),
      })
      if not diff_id:
        diff_id = docker_digest.SHA256(self.uncompressed_blob(self._blob_sum))

      # Takes naked hex.
      overrides = overrides.Override(layers=[diff_id[len('sha256:'):]])
    else:
      # The empty layer.
      overrides = overrides.Override(layers=[docker_digest.SHA256(b'', '')])

    config_file = metadata.Override(config_file, overrides)

    self._config_file = json.dumps(config_file, sort_keys=True)
    utf8_encoded_config = self._config_file.encode('utf8')
    manifest['config']['digest'] = docker_digest.SHA256(utf8_encoded_config)
    manifest['config']['size'] = len(utf8_encoded_config)
    self._manifest = json.dumps(manifest, sort_keys=True)

  def manifest(self):
    """Override."""
    return self._manifest

  def config_file(self):
    """Override."""
    return self._config_file

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
