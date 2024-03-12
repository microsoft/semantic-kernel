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
"""This package provides compatibility interfaces for OCI."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import json

from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from containerregistry.client.v2_2 import docker_image_list



class OCIFromV22(docker_image.Delegate):
  """This compatibility interface serves an OCI image from a v2_2 image."""

  def manifest(self):
    """Override."""
    manifest = json.loads(self._image.manifest())

    manifest['mediaType'] = docker_http.OCI_MANIFEST_MIME
    manifest['config']['mediaType'] = docker_http.OCI_CONFIG_JSON_MIME
    for layer in manifest['layers']:
      layer['mediaType'] = docker_http.OCI_LAYER_MIME

    return json.dumps(manifest, sort_keys=True)

  def media_type(self):
    """Override."""
    return docker_http.OCI_MANIFEST_MIME

  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    pass


class V22FromOCI(docker_image.Delegate):
  """This compatibility interface serves a v2_2 image from an OCI image."""

  def manifest(self):
    """Override."""
    manifest = json.loads(self._image.manifest())

    manifest['mediaType'] = docker_http.MANIFEST_SCHEMA2_MIME
    manifest['config']['mediaType'] = docker_http.CONFIG_JSON_MIME
    for layer in manifest['layers']:
      layer['mediaType'] = docker_http.LAYER_MIME

    return json.dumps(manifest, sort_keys=True)

  def media_type(self):
    """Override."""
    return docker_http.MANIFEST_SCHEMA2_MIME

  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    pass


class IndexFromList(docker_image_list.Delegate):
  """This compatibility interface serves an Image Index from a Manifest List."""

  def __init__(self,
               image,
               recursive = True):
    """Constructor.

    Args:
      image: a DockerImageList on which __enter__ has already been called.
      recursive: whether to recursively convert child manifests to OCI types.
    """
    super(IndexFromList, self).__init__(image)
    self._recursive = recursive

  def manifest(self):
    """Override."""
    manifest = json.loads(self._image.manifest())
    manifest['mediaType'] = docker_http.OCI_IMAGE_INDEX_MIME
    return json.dumps(manifest, sort_keys=True)

  def media_type(self):
    """Override."""
    return docker_http.OCI_IMAGE_INDEX_MIME

  def __enter__(self):
    if not self._recursive:
      return self

    converted = []
    for platform, child in self._image:
      if isinstance(child, docker_image_list.DockerImageList):
        with IndexFromList(child) as index:
          converted.append((platform, index))
      else:
        assert isinstance(child, docker_image.DockerImage)
        with OCIFromV22(child) as oci:
          converted.append((platform, oci))
    with docker_image_list.FromList(converted) as index:
      self._image = index
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    pass


class ListFromIndex(docker_image_list.Delegate):
  """This compatibility interface serves a Manifest List from an Image Index."""

  def __init__(self,
               image,
               recursive = True):
    """Constructor.

    Args:
      image: a DockerImageList on which __enter__ has already been called.
      recursive: whether to recursively convert child manifests to Docker types.
    """
    super(ListFromIndex, self).__init__(image)
    self._recursive = recursive

  def manifest(self):
    """Override."""
    manifest = json.loads(self._image.manifest())
    manifest['mediaType'] = docker_http.MANIFEST_LIST_MIME
    return json.dumps(manifest, sort_keys=True)

  def media_type(self):
    """Override."""
    return docker_http.MANIFEST_LIST_MIME

  def __enter__(self):
    if not self._recursive:
      return self

    converted = []
    for platform, child in self._image:
      if isinstance(child, docker_image_list.DockerImageList):
        with ListFromIndex(child) as image_list:
          converted.append((platform, image_list))
      else:
        assert isinstance(child, docker_image.DockerImage)
        with V22FromOCI(child) as v22:
          converted.append((platform, v22))
    with docker_image_list.FromList(converted) as image_list:
      self._image = image_list
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    pass
