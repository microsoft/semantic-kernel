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
"""This package provides compatibility interfaces for v1/v2."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import json

from containerregistry.client.v2 import docker_image as v2_image
from containerregistry.client.v2 import util as v2_util
from containerregistry.client.v2_2 import docker_digest
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image as v2_2_image



class BadDigestException(Exception):
  """Exceptions when a bad digest is supplied."""


EMPTY_TAR_DIGEST = 'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4'
EMPTY_TAR_BYTES = b'\x1f\x8b\x08\x00\x00\tn\x88\x00\xffb\x18\x05\xa3`\x14\x8cX\x00\x08\x00\x00\xff\xff.\xaf\xb5\xef\x00\x04\x00\x00'  # pylint: disable=line-too-long



# Expose a way of constructing the config file given just the v1 compat list
# and a list of diff ids.  This is used for compatibility with v2 images (below)
# but is also useful for scenarios where we are handling 'docker save' tarballs
# since those don't know their v2/v2.2 blob names and gzipping to compute them
# is wasteful because we don't actually need them if we are just going to
# re-save the image.  While we don't provide it here, this can be used to
# synthesize a v2.2 config_file directly from a v1.docker_image.DockerImage.
def config_file(v1_compats,
                diff_ids):
  """Compute the v2.2 config file given the history and diff ids."""
  # We want the first (last reversed) v1 compatibility field, from which
  # we will draw additional fields.
  v1_compatibility = {}
  histories = []
  for v1_compat in v1_compats:
    v1_compatibility = v1_compat

    # created_by in history is the cmd which was run to create the layer.
    # Cmd in container config may be empty array.
    history = {}
    if 'container_config' in v1_compatibility:
      container_config = v1_compatibility.get('container_config')
      if container_config.get('Cmd'):  # pytype: disable=attribute-error
        history['created_by'] = container_config['Cmd'][0]

    if 'created' in v1_compatibility:
      history['created'] = v1_compatibility.get('created')

    histories += [history]

  config = {
      'history': histories,
      'rootfs': {
          'diff_ids': diff_ids,
          'type': 'layers'
      }
  }

  for key in [
      'architecture', 'config', 'container', 'container_config',
      'docker_version', 'os'
  ]:
    if key in v1_compatibility:
      config[key] = v1_compatibility[key]

  if 'created' in v1_compatibility:
    config['created'] = v1_compatibility.get('created')

  return json.dumps(config, sort_keys=True)


class V22FromV2(v2_2_image.DockerImage):
  """This compatibility interface serves the v2 interface from a v2_2 image."""

  def __init__(self, v2_img):
    """Constructor.

    Args:
      v2_img: a v2 DockerImage on which __enter__ has already been called.

    Raises:
      ValueError: an incorrectly typed argument was supplied.
    """
    self._v2_image = v2_img
    self._ProcessImage()

  def _ProcessImage(self):
    """Constructs schema 2 manifest from schema 1 manifest."""
    raw_manifest_schema1 = self._v2_image.manifest()
    manifest_schema1 = json.loads(raw_manifest_schema1)

    self._config_file = config_file([
        json.loads(history.get('v1Compatibility', '{}'))
        for history in reversed(manifest_schema1.get('history', []))
    ], [
        self._GetDiffId(digest)
        for digest in reversed(self._v2_image.fs_layers())
    ])

    config_bytes = self._config_file.encode('utf8')
    config_descriptor = {
        'mediaType': docker_http.CONFIG_JSON_MIME,
        'size': len(config_bytes),
        'digest': docker_digest.SHA256(config_bytes)
    }

    manifest_schema2 = {
        'schemaVersion': 2,
        'mediaType': docker_http.MANIFEST_SCHEMA2_MIME,
        'config': config_descriptor,
        'layers': [
            {
                'mediaType': docker_http.LAYER_MIME,
                'size': self._v2_image.blob_size(digest),
                'digest': digest
            }
            for digest in reversed(self._v2_image.fs_layers())
        ]
    }
    self._manifest = json.dumps(manifest_schema2, sort_keys=True)

  def _GetDiffId(self, digest):
    """Hash the uncompressed layer blob."""
    return docker_digest.SHA256(self._v2_image.uncompressed_blob(digest))

  def manifest(self):
    """Override."""
    return self._manifest

  def config_file(self):
    """Override."""
    return self._config_file

  def uncompressed_blob(self, digest):
    """Override."""
    return self._v2_image.uncompressed_blob(digest)

  def blob(self, digest):
    """Override."""
    return self._v2_image.blob(digest)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


class V2FromV22(v2_image.DockerImage):
  """This compatibility interface serves the v2 interface from a v2_2 image."""

  def __init__(self, v2_2_img):
    """Constructor.

    Args:
      v2_2_img: a v2_2 DockerImage on which __enter__ has already been called.

    Raises:
      ValueError: an incorrectly typed argument was supplied.
    """
    self._v2_2_image = v2_2_img
    self._ProcessImage()

  def _ProcessImage(self):
    """Constructs schema 1 manifest from schema 2 manifest and config file."""
    manifest_schema2 = json.loads(self._v2_2_image.manifest())
    raw_config = self._v2_2_image.config_file()
    config = json.loads(raw_config)

    parent = ''

    histories = config.get('history', {})
    layer_count = len(histories)
    v2_layer_index = 0
    layers = manifest_schema2.get('layers', {})

    # from base to top
    fs_layers = []
    v1_histories = []
    for v1_layer_index, history in enumerate(histories):
      digest, media_type, v2_layer_index = self._GetSchema1LayerDigest(
          history, layers, v1_layer_index, v2_layer_index)

      if v1_layer_index != layer_count - 1:
        layer_id = self._GenerateV1LayerId(digest, parent)
        v1_compatibility = self._BuildV1Compatibility(layer_id, parent, history)
      else:
        layer_id = self._GenerateV1LayerId(digest, parent, raw_config)
        v1_compatibility = self._BuildV1CompatibilityForTopLayer(
            layer_id, parent, history, config)
      parent = layer_id
      fs_layers = [{'blobSum': digest, 'mediaType': media_type}] + fs_layers
      v1_histories = [{'v1Compatibility': v1_compatibility}] + v1_histories

    manifest_schema1 = {
        'schemaVersion': 1,
        'name': 'unused',
        'tag': 'unused',
        'fsLayers': fs_layers,
        'history': v1_histories
    }
    if 'architecture' in config:
      manifest_schema1['architecture'] = config['architecture']
    self._manifest = v2_util.Sign(json.dumps(manifest_schema1, sort_keys=True))

  def _GenerateV1LayerId(self,
                         digest,
                         parent,
                         raw_config = None):
    parts = digest.rsplit(':', 1)
    if len(parts) != 2:
      raise BadDigestException('Invalid Digest: %s, must be in '
                               'algorithm : blobSumHex format.' % (digest))

    data = parts[1] + ' ' + parent

    if raw_config:
      data += ' ' + raw_config
    return docker_digest.SHA256(data.encode('utf8'), '')

  def _BuildV1Compatibility(self, layer_id, parent,
                            history):
    v1_compatibility = {'id': layer_id}

    if parent:
      v1_compatibility['parent'] = parent

    if 'empty_layer' in history:
      v1_compatibility['throwaway'] = True

    if 'created_by' in history:
      v1_compatibility['container_config'] = {'Cmd': [history['created_by']]}

    for key in ['created', 'comment', 'author']:
      if key in history:
        v1_compatibility[key] = history[key]

    return json.dumps(v1_compatibility, sort_keys=True)

  def _BuildV1CompatibilityForTopLayer(self, layer_id, parent,
                                       history,
                                       config):
    v1_compatibility = {'id': layer_id}

    if parent:
      v1_compatibility['parent'] = parent

    if 'empty_layer' in history:
      v1_compatibility['throwaway'] = True

    for key in [
        'architecture', 'container', 'docker_version', 'os', 'config',
        'container_config', 'created'
    ]:
      if key in config:
        v1_compatibility[key] = config[key]

    return json.dumps(v1_compatibility, sort_keys=True)

  def _GetSchema1LayerDigest(
      self, history, layers,
      v1_layer_index, v2_layer_index):
    if 'empty_layer' in history:
      return (EMPTY_TAR_DIGEST, docker_http.LAYER_MIME, v2_layer_index)
    else:
      return (
          layers[v2_layer_index]['digest'],
          layers[v2_layer_index]['mediaType'],
          v2_layer_index + 1
      )

  def manifest(self):
    """Override."""
    return self._manifest

  def uncompressed_blob(self, digest):
    """Override."""
    if digest == EMPTY_TAR_DIGEST:
      # See comment in blob().
      return super(V2FromV22, self).uncompressed_blob(EMPTY_TAR_DIGEST)
    return self._v2_2_image.uncompressed_blob(digest)

  def diff_id(self, digest):
    """Gets v22 diff_id."""
    return self._v2_2_image.digest_to_diff_id(digest)

  def blob(self, digest):
    """Override."""
    if digest == EMPTY_TAR_DIGEST:
      # We added this blobsum for 'empty_layer' annotated layers, but the
      # underlying v2.2 image doesn't necessarily expose them.  So
      # when we get a request for this special layer, return the raw
      # bytes ourselves.
      return EMPTY_TAR_BYTES
    return self._v2_2_image.blob(digest)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass
