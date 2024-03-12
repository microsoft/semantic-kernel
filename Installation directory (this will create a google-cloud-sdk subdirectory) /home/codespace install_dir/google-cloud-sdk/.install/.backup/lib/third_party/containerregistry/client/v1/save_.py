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
"""This package provides tools for saving docker images."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import io
import json
import tarfile

from containerregistry.client import docker_name
from containerregistry.client.v1 import docker_image

import six



def multi_image_tarball(
    tag_to_image,
    tar):
  """Produce a "docker save" compatible tarball from the DockerImages.

  Args:
    tag_to_image: A dictionary of tags to the images they label.
    tar: the open tarfile into which we are writing the image tarball.
  """

  def add_file(filename, contents):
    info = tarfile.TarInfo(filename)
    info.size = len(contents)
    tar.addfile(tarinfo=info, fileobj=io.BytesIO(contents))

  seen = set()
  repositories = {}
  # Each layer is encoded as a directory in the larger tarball of the form:
  #  {layer_id}\
  #    layer.tar
  #    VERSION
  #    json
  for (tag, image) in six.iteritems(tag_to_image):
    # Add this image's repositories entry.
    repo = str(tag.as_repository())
    tags = repositories.get(repo, {})
    tags[tag.tag] = image.top()
    repositories[repo] = tags

    for layer_id in image.ancestry(image.top()):
      # Add each layer_id exactly once.
      if layer_id in seen or json.loads(image.json(layer_id)).get('throwaway'):
        continue
      seen.add(layer_id)

      # VERSION generally seems to contain 1.0, not entirely sure
      # what the point of this is.
      add_file(layer_id + '/VERSION', b'1.0')

      # Add the unzipped layer tarball
      content = image.uncompressed_layer(layer_id)
      add_file(layer_id + '/layer.tar', content)

      # Now the json metadata
      add_file(layer_id + '/json', image.json(layer_id).encode('utf8'))

  # Add the metadata tagging the top layer.
  add_file('repositories',
           json.dumps(repositories, sort_keys=True).encode('utf8'))


def tarball(name, image,
            tar):
  """Produce a "docker save" compatible tarball from the DockerImage.

  Args:
    name: The tag name to write into the repositories file.
    image: a docker image to save.
    tar: the open tarfile into which we are writing the image tarball.
  """

  def add_file(filename, contents):
    info = tarfile.TarInfo(filename)
    info.size = len(contents)
    tar.addfile(tarinfo=info, fileobj=io.BytesIO(contents))

  multi_image_tarball({name: image}, tar)

  # Add our convenience file with the top layer's ID.
  add_file('top', image.top().encode('utf8'))
