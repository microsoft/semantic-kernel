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
"""This package manages pushes to and deletes from a v2 docker registry."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import logging
import concurrent.futures

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_http
from containerregistry.client.v2 import docker_image

import httplib2

import six.moves.http_client
import six.moves.urllib.parse


def _tag_or_digest(name):
  if isinstance(name, docker_name.Tag):
    return name.tag
  else:
    assert isinstance(name, docker_name.Digest)
    return name.digest


class Push(object):
  """Push encapsulates a Registry v2 Docker push session."""

  def __init__(self,
               name,
               creds,
               transport,
               mount = None,
               threads = 1):
    """Constructor.

    If multiple threads are used, the caller *must* ensure that the provided
    transport is thread-safe, as well as the image that is being uploaded.
    It is notable that tarfile and httplib2.Http in Python are NOT threadsafe.

    Args:
      name: the fully-qualified name of the tag to push
      creds: provider for authorizing requests
      transport: the http transport to use for sending requests
      mount: list of repos from which to mount blobs.
      threads: the number of threads to use for uploads.

    Raises:
      ValueError: an incorrectly typed argument was supplied.
    """
    self._name = name
    self._transport = docker_http.Transport(name, creds, transport,
                                            docker_http.PUSH)
    self._mount = mount
    self._threads = threads

  def name(self):
    return self._name

  def _scheme_and_host(self):
    return '{scheme}://{registry}'.format(
        scheme=docker_http.Scheme(self._name.registry),
        registry=self._name.registry)

  def _base_url(self):
    return self._scheme_and_host() + '/v2/{repository}'.format(
        repository=self._name.repository)

  def _get_absolute_url(self, location):
    # If 'location' is an absolute URL (includes host), this will be a no-op.
    return six.moves.urllib.parse.urljoin(
        base=self._scheme_and_host(), url=location)

  def blob_exists(self, digest):
    """Check the remote for the given layer."""
    # HEAD the blob, and check for a 200
    resp, unused_content = self._transport.Request(
        '{base_url}/blobs/{digest}'.format(
            base_url=self._base_url(), digest=digest),
        method='HEAD',
        accepted_codes=[
            six.moves.http_client.OK, six.moves.http_client.NOT_FOUND
        ])

    return resp.status == six.moves.http_client.OK  # pytype: disable=attribute-error

  def manifest_exists(self, image):
    """Check the remote for the given manifest by digest."""
    # GET the manifest by digest, and check for 200
    resp, unused_content = self._transport.Request(
        '{base_url}/manifests/{digest}'.format(
            base_url=self._base_url(), digest=image.digest()),
        method='GET',
        accepted_codes=[
            six.moves.http_client.OK, six.moves.http_client.NOT_FOUND
        ])

    return resp.status == six.moves.http_client.OK  # pytype: disable=attribute-error

  def _monolithic_upload(self, image,
                         digest):
    self._transport.Request(
        '{base_url}/blobs/uploads/?digest={digest}'.format(
            base_url=self._base_url(), digest=digest),
        method='POST',
        body=image.blob(digest),
        accepted_codes=[six.moves.http_client.CREATED])

  def _add_digest(self, url, digest):
    scheme, netloc, path, query_string, fragment = (
        six.moves.urllib.parse.urlsplit(url))
    qs = six.moves.urllib.parse.parse_qs(query_string)
    qs['digest'] = [digest]
    query_string = six.moves.urllib.parse.urlencode(qs, doseq=True)
    return six.moves.urllib.parse.urlunsplit((scheme, netloc, path,
                                              query_string, fragment))

  def _put_upload(self, image, digest):
    mounted, location = self._start_upload(digest, self._mount)

    if mounted:
      logging.info('Layer %s mounted.', digest)
      return

    location = self._add_digest(location, digest)
    self._transport.Request(
        location,
        method='PUT',
        body=image.blob(digest),
        accepted_codes=[six.moves.http_client.CREATED])

  # pylint: disable=missing-docstring
  def patch_upload(self, source,
                   digest):
    mounted, location = self._start_upload(digest, self._mount)

    if mounted:
      logging.info('Layer %s mounted.', digest)
      return

    location = self._get_absolute_url(location)
    blob = source
    if isinstance(source, docker_image.DockerImage):
      blob = source.blob(digest)

    resp, unused_content = self._transport.Request(
        location,
        method='PATCH',
        body=blob,
        content_type='application/octet-stream',
        accepted_codes=[
            six.moves.http_client.NO_CONTENT, six.moves.http_client.ACCEPTED,
            six.moves.http_client.CREATED
        ])

    location = self._add_digest(resp['location'], digest)
    location = self._get_absolute_url(location)
    self._transport.Request(
        location,
        method='PUT',
        body=None,
        accepted_codes=[six.moves.http_client.CREATED])

  def _put_blob(self, image, digest):
    """Upload the aufs .tgz for a single layer."""
    # We have a few choices for unchunked uploading:
    #   POST to /v2/<name>/blobs/uploads/?digest=<digest>
    #   Fastest, but not supported by many registries.
    # self._monolithic_upload(image, digest)
    #
    # or:
    #   POST /v2/<name>/blobs/uploads/        (no body*)
    #   PUT  /v2/<name>/blobs/uploads/<uuid>  (full body)
    #   Next fastest, but there is a mysterious bad interaction
    #   with Bintray.  This pattern also hasn't been used in
    #   clients since 1.8, when they switched to the 3-stage
    #   method below.
    # self._put_upload(image, digest)
    # or:
    #   POST   /v2/<name>/blobs/uploads/        (no body*)
    #   PATCH  /v2/<name>/blobs/uploads/<uuid>  (full body)
    #   PUT    /v2/<name>/blobs/uploads/<uuid>  (no body)
    #
    # * We attempt to perform a cross-repo mount if any repositories are
    # specified in the "mount" parameter. This does a fast copy from a
    # repository that is known to contain this blob and skips the upload.
    self.patch_upload(image, digest)

  def _remote_tag_digest(self):
    """Check the remote for the given manifest by digest."""

    # GET the tag we're pushing
    resp, unused_content = self._transport.Request(
        '{base_url}/manifests/{tag}'.format(
            base_url=self._base_url(),
            tag=self._name.tag),  # pytype: disable=attribute-error
        method='GET',
        accepted_codes=[
            six.moves.http_client.OK, six.moves.http_client.NOT_FOUND
        ])

    if resp.status == six.moves.http_client.NOT_FOUND:  # pytype: disable=attribute-error
      return None

    return resp.get('docker-content-digest')

  def put_manifest(self, image):
    """Upload the manifest for this image."""
    self._transport.Request(
        '{base_url}/manifests/{tag_or_digest}'.format(
            base_url=self._base_url(),
            tag_or_digest=_tag_or_digest(self._name)),
        method='PUT',
        body=image.manifest().encode('utf8'),
        accepted_codes=[
            six.moves.http_client.OK, six.moves.http_client.CREATED,
            six.moves.http_client.ACCEPTED
        ])

  def _start_upload(self,
                    digest,
                    mount = None
                   ):
    """POST to begin the upload process with optional cross-repo mount param."""
    if not mount:
      # Do a normal POST to initiate an upload if mount is missing.
      url = '{base_url}/blobs/uploads/'.format(base_url=self._base_url())
      accepted_codes = [six.moves.http_client.ACCEPTED]
    else:
      # If we have a mount parameter, try to mount the blob from another repo.
      mount_from = '&'.join([
          'from=' + six.moves.urllib.parse.quote(repo.repository, '')
          for repo in self._mount
      ])
      url = '{base_url}/blobs/uploads/?mount={digest}&{mount_from}'.format(
          base_url=self._base_url(), digest=digest, mount_from=mount_from)
      accepted_codes = [
          six.moves.http_client.CREATED, six.moves.http_client.ACCEPTED
      ]

    resp, unused_content = self._transport.Request(
        url, method='POST', body=None, accepted_codes=accepted_codes)
    # pytype: disable=attribute-error,bad-return-type
    return resp.status == six.moves.http_client.CREATED, resp.get('location')
    # pytype: enable=attribute-error,bad-return-type

  def _upload_one(self, image, digest):
    """Upload a single layer, after checking whether it exists already."""
    if self.blob_exists(digest):
      logging.info('Layer %s exists, skipping', digest)
      return

    self._put_blob(image, digest)
    logging.info('Layer %s pushed.', digest)

  def upload(self, image):
    """Upload the layers of the given image.

    Args:
      image: the image to upload.
    """
    # If the manifest (by digest) exists, then avoid N layer existence
    # checks (they must exist).
    if self.manifest_exists(image):
      if isinstance(self._name, docker_name.Tag):
        if self._remote_tag_digest() == image.digest():
          logging.info('Tag points to the right manifest, skipping push.')
          return
        logging.info('Manifest exists, skipping blob uploads and pushing tag.')
      else:
        logging.info('Manifest exists, skipping upload.')
    elif self._threads == 1:
      for digest in image.blob_set():
        self._upload_one(image, digest)
    else:
      with concurrent.futures.ThreadPoolExecutor(
          max_workers=self._threads) as executor:
        future_to_params = {
            executor.submit(self._upload_one, image, digest): (image, digest)
            for digest in image.blob_set()
        }
        for future in concurrent.futures.as_completed(future_to_params):
          future.result()

    # This should complete the upload by uploading the manifest.
    self.put_manifest(image)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, exception_type, unused_value, unused_traceback):
    if exception_type:
      logging.error('Error during upload of: %s', self._name)
      return
    logging.info('Finished upload of: %s', self._name)


# pylint: disable=invalid-name
def Delete(name,
           creds, transport):
  """Delete a tag or digest.

  Args:
    name: a tag or digest to be deleted.
    creds: the credentials to use for deletion.
    transport: the transport to use to contact the registry.
  """
  docker_transport = docker_http.Transport(name, creds, transport,
                                           docker_http.DELETE)

  _, unused_content = docker_transport.Request(
      '{scheme}://{registry}/v2/{repository}/manifests/{entity}'.format(
          scheme=docker_http.Scheme(name.registry),
          registry=name.registry,
          repository=name.repository,
          entity=_tag_or_digest(name)),
      method='DELETE',
      accepted_codes=[six.moves.http_client.OK, six.moves.http_client.ACCEPTED])
