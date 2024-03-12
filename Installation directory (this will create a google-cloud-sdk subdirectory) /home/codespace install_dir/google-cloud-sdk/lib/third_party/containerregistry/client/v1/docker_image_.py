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

import abc
import gzip
import io
import json
import os
import string
import subprocess
import sys
import tarfile
import tempfile
import threading

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v1 import docker_creds as v1_creds
from containerregistry.client.v1 import docker_http

import httplib2

import six
from six.moves import range  # pylint: disable=redefined-builtin
import six.moves.http_client


class DockerImage(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for implementations that interact with Docker images."""

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def top(self):
    """The layer id of the topmost layer."""
  # pytype: enable=bad-return-type

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def repositories(self):
    """The json blob of tags, loaded as a dict."""
    pass
  # pytype: enable=bad-return-type

  def parent(self, layer_id):
    """The layer of id of the parent of the provided layer, or None.

    Args:
      layer_id: the id of the layer whose parentage we're asking

    Returns:
      The identity of the parent layer, or None if the root.
    """
    metadata = json.loads(self.json(layer_id))
    if 'parent' not in metadata:
      return None
    return metadata['parent']

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def json(self, layer_id):
    """The JSON metadata of the provided layer.

    Args:
      layer_id: the id of the layer whose metadata we're asking

    Returns:
      The raw json string of the layer.
    """
    pass
  # pytype: enable=bad-return-type

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def layer(self, layer_id):
    """The layer.tar.gz blob of the provided layer id.

    Args:
      layer_id: the id of the layer for whose layer blob we're asking

    Returns:
      The raw blob string of the layer.
    """
    pass
  # pytype: enable=bad-return-type

  def uncompressed_layer(self, layer_id):
    """Same as layer() but uncompressed."""
    zipped = self.layer(layer_id)
    buf = io.BytesIO(zipped)
    f = gzip.GzipFile(mode='rb', fileobj=buf)
    unzipped = f.read()
    return unzipped

  def diff_id(self, digest):
    """diff_id only exist in schema v22."""
    return None

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def ancestry(self, layer_id):
    """The ancestry of the given layer, base layer first.

    Args:
      layer_id: the id of the layer whose ancestry we're asking

    Returns:
      The list of ancestor IDs, base first, layer_id last.
    """
    pass
  # pytype: enable=bad-return-type

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    pass

  @abc.abstractmethod
  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


# Gzip injects a timestamp into its output, which makes its output and digest
# non-deterministic.  To get reproducible pushes, freeze time.
# This approach is based on the following StackOverflow answer:
# http://stackoverflow.com/
#    questions/264224/setting-the-gzip-timestamp-from-python
class _FakeTime(object):

  def time(self):
    return 1225856967.109


gzip.time = _FakeTime()


class FromShardedTarball(DockerImage):
  """This decodes the sharded image tarballs from docker_build."""

  def __init__(self,
               layer_to_tarball,
               top,
               name = None,
               compresslevel = 9):
    self._layer_to_tarball = layer_to_tarball
    self._top = top
    self._compresslevel = compresslevel
    self._memoize = {}
    self._lock = threading.Lock()
    self._name = name

  def _content(self, layer_id, name, memoize = True):
    """Fetches a particular path's contents from the tarball."""
    # Check our cache
    if memoize:
      with self._lock:
        if name in self._memoize:
          return self._memoize[name]

    # tarfile is inherently single-threaded:
    # https://mail.python.org/pipermail/python-bugs-list/2015-March/265999.html
    # so instead of locking, just open the tarfile for each file
    # we want to read.
    with tarfile.open(name=self._layer_to_tarball(layer_id), mode='r:') as tar:
      try:
        content = tar.extractfile(name).read()  # pytype: disable=attribute-error
      except KeyError:
        content = tar.extractfile('./' + name).read()  # pytype: disable=attribute-error

      # Populate our cache.
      if memoize:
        with self._lock:
          self._memoize[name] = content
      return content

  def top(self):
    """Override."""
    return self._top

  def repositories(self):
    """Override."""
    return json.loads(self._content(self.top(), 'repositories').decode('utf8'))

  def json(self, layer_id):
    """Override."""
    return self._content(layer_id, layer_id + '/json').decode('utf8')

  # Large, do not memoize.
  def uncompressed_layer(self, layer_id):
    """Override."""
    return self._content(layer_id, layer_id + '/layer.tar', memoize=False)

  # Large, do not memoize.
  def layer(self, layer_id):
    """Override."""
    unzipped = self.uncompressed_layer(layer_id)
    buf = io.BytesIO()
    f = gzip.GzipFile(mode='wb', compresslevel=self._compresslevel, fileobj=buf)
    try:
      f.write(unzipped)
    finally:
      f.close()

    zipped = buf.getvalue()
    return zipped

  def ancestry(self, layer_id):
    """Override."""
    p = self.parent(layer_id)
    if not p:
      return [layer_id]
    return [layer_id] + self.ancestry(p)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


def _get_top(tarball, name = None):
  """Get the topmost layer in the image tarball."""
  with tarfile.open(name=tarball, mode='r:') as tar:
    reps = tar.extractfile('repositories') or tar.extractfile('./repositories')
    if reps is None:
      raise ValueError('Tarball must contain a repositories file')
    repositories = json.loads(reps.read().decode('utf8'))

  if name:
    key = str(name.as_repository())
    return repositories[key][name.tag]

  if len(repositories) != 1:
    raise ValueError('Tarball must contain a single repository, '
                     'or a name must be specified to FromTarball.')

  for (unused_repo, tags) in six.iteritems(repositories):
    if len(tags) != 1:
      raise ValueError('Tarball must contain a single tag, '
                       'or a name must be specified to FromTarball.')
    for (unused_tag, layer_id) in six.iteritems(tags):
      return layer_id

  raise Exception('Unreachable code in _get_top()')


class FromTarball(FromShardedTarball):
  """This decodes the image tarball output of docker_build for upload."""

  def __init__(self,
               tarball,
               name = None,
               compresslevel = 9):
    super(FromTarball, self).__init__(
        lambda unused_id: tarball,
        _get_top(tarball, name),
        name=name,
        compresslevel=compresslevel)


class FromRegistry(DockerImage):
  """This accesses a docker image hosted on a registry (non-local)."""

  def __init__(
      self,
      name,
      basic_creds,
      transport):
    self._name = name
    self._creds = basic_creds
    self._transport = transport
    # Set up in __enter__
    self._tags = {}
    self._response = {}

  def top(self):
    """Override."""
    assert isinstance(self._name, docker_name.Tag)
    return self._tags[self._name.tag]

  def repositories(self):
    """Override."""
    return {self._name.repository: self._tags}

  def tags(self):
    """Lists the tags present in the remote repository."""
    return list(self.raw_tags().keys())

  def raw_tags(self):
    """Dictionary of tag to image id."""
    return self._tags

  def _content(self, suffix):
    if suffix not in self._response:
      _, self._response[suffix] = docker_http.Request(
          self._transport, '{scheme}://{endpoint}/v1/images/{suffix}'.format(
              scheme=docker_http.Scheme(self._endpoint),
              endpoint=self._endpoint,
              suffix=suffix), self._creds, [six.moves.http_client.OK])
    return self._response[suffix]

  def json(self, layer_id):
    """Override."""
    # GET server1/v1/images/IMAGEID/json
    return self._content(layer_id + '/json').decode('utf8')

  # Large, do not memoize.
  def layer(self, layer_id):
    """Override."""
    # GET server1/v1/images/IMAGEID/layer
    return self._content(layer_id + '/layer')

  def ancestry(self, layer_id):
    """Override."""
    # GET server1/v1/images/IMAGEID/ancestry
    return json.loads(self._content(layer_id + '/ancestry').decode('utf8'))

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # This initiates the pull by issuing:
    #   GET H:P/v1/repositories/R/images
    resp, unused_content = docker_http.Request(
        self._transport,
        '{scheme}://{registry}/v1/repositories/{repository_name}/images'.format(
            scheme=docker_http.Scheme(self._name.registry),
            registry=self._name.registry,
            repository_name=self._name.repository), self._creds,
        [six.moves.http_client.OK])

    # The response should have an X-Docker-Token header, which
    # we should extract and annotate subsequent requests with:
    #   Authorization: Token {extracted value}
    self._creds = v1_creds.Token(resp['x-docker-token'])

    self._endpoint = resp['x-docker-endpoints']
    # TODO(user): Consider also supporting cookies, which are
    # used by Quay.io for authenticated sessions.

    # Next, fetch the set of tags in this repository.
    #   GET server1/v1/repositories/R/tags
    resp, content = docker_http.Request(
        self._transport,
        '{scheme}://{endpoint}/v1/repositories/{repository_name}/tags'.format(
            scheme=docker_http.Scheme(self._endpoint),
            endpoint=self._endpoint,
            repository_name=self._name.repository), self._creds,
        [six.moves.http_client.OK])

    self._tags = json.loads(content.decode('utf8'))
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


class Random(DockerImage):
  """This generates an image with Random properties.

  We ensure basic consistency of the generated docker
  image.
  """

  # TODO(b/36589467): Add function arg for creating blob.
  def __init__(self,
               sample,
               num_layers = 5,
               layer_byte_size = 64,
               blobs = None):
    # Generate the image.
    self._ancestry = []
    self._layers = {}

    num_layers = len(blobs) if blobs else num_layers
    for i in range(num_layers):
      # Avoid repetitions.
      while True:
        layer_id = self._next_id(sample)
        if layer_id not in self._ancestry:
          self._ancestry += [layer_id]
          blob = blobs[i] if blobs else None
          self._layers[layer_id] = self._next_layer(
              sample, layer_byte_size, blob)
          break

  def top(self):
    """Override."""
    return self._ancestry[0]

  def repositories(self):
    """Override."""
    return {'random/image': {'latest': self.top(),}}

  def json(self, layer_id):
    """Override."""
    metadata = {'id': layer_id}

    ancestry = self.ancestry(layer_id)
    if len(ancestry) != 1:
      metadata['parent'] = ancestry[1]

    return json.dumps(metadata, sort_keys=True)

  def layer(self, layer_id):
    """Override."""
    return self._layers[layer_id]

  def ancestry(self, layer_id):
    """Override."""
    assert layer_id in self._ancestry
    index = self._ancestry.index(layer_id)
    return self._ancestry[index:]

  def _next_id(self, sample):
    return sample(b'0123456789abcdef', 64).decode('utf8')

  # pylint: disable=missing-docstring
  def _next_layer(self, sample,
                  layer_byte_size, blob):
    buf = io.BytesIO()

    # TODO(user): Consider doing something more creative...
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
      if blob:
        info = tarfile.TarInfo(name='./'+self._next_id(sample))
        info.size = len(blob)
        tar.addfile(info, fileobj=io.BytesIO(blob))
      # Linux optimization, use dd for data file creation.
      elif sys.platform.startswith('linux') and layer_byte_size >= 1024 * 1024:
        mb = layer_byte_size / (1024 * 1024)
        tempdir = tempfile.mkdtemp()
        data_filename = os.path.join(tempdir, 'a.bin')
        if os.path.exists(data_filename):
          os.remove(data_filename)

        process = subprocess.Popen([
            'dd', 'if=/dev/urandom',
            'of=%s' % data_filename, 'bs=1M',
            'count=%d' % mb
        ])
        process.wait()

        with io.open(data_filename, u'rb') as fd:
          info = tar.gettarinfo(name=data_filename)
          tar.addfile(info, fileobj=fd)
          os.remove(data_filename)
          os.rmdir(tempdir)
      else:
        data = sample(string.printable.encode('utf8'), layer_byte_size)
        info = tarfile.TarInfo(name='./' + self._next_id(sample))
        info.size = len(data)
        tar.addfile(info, fileobj=io.BytesIO(data))

    return buf.getvalue()

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass
