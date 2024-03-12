# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Helpers for accessing GCS.

Bulk object uploads and downloads use methods that shell out to gsutil.
Lightweight metadata / streaming operations use the StorageClient class.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import sys

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import transfer

from googlecloudsdk.api_lib.dataproc import exceptions as dp_exceptions
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six.moves.urllib.parse


# URI scheme for GCS.
STORAGE_SCHEME = 'gs'

# Timeout for individual socket connections. Matches gsutil.
HTTP_TIMEOUT = 60

# Fix urlparse for storage paths.
# This allows using urljoin in other files (that import this).
six.moves.urllib.parse.uses_relative.append(STORAGE_SCHEME)
six.moves.urllib.parse.uses_netloc.append(STORAGE_SCHEME)


def Upload(files, destination, storage_client=None):
  # TODO(b/109938541): Remove gsutil implementation after the new
  # implementation seems stable.
  use_gsutil = properties.VALUES.storage.use_gsutil.GetBool()
  if use_gsutil:
    _UploadGsutil(files, destination)
  else:
    _UploadStorageClient(files, destination, storage_client=storage_client)


def _UploadStorageClient(files, destination, storage_client=None):
  """Upload a list of local files to GCS.

  Args:
    files: The list of local files to upload.
    destination: A GCS "directory" to copy the files into.
    storage_client: Storage api client used to copy files to gcs.
  """
  client = storage_client or storage_api.StorageClient()
  for file_to_upload in files:
    file_name = os.path.basename(file_to_upload)
    dest_url = os.path.join(destination, file_name)
    dest_object = storage_util.ObjectReference.FromUrl(dest_url)
    try:
      client.CopyFileToGCS(file_to_upload, dest_object)
    except exceptions.BadFileException as err:
      raise dp_exceptions.FileUploadError(
          "Failed to upload files ['{}'] to '{}': {}".format(
              "', '".join(files), destination, err))


def _UploadGsutil(files, destination):
  """Upload a list of local files to GCS.

  Args:
    files: The list of local files to upload.
    destination: A GCS "directory" to copy the files into.
  """
  args = files
  args += [destination]
  exit_code = storage_util.RunGsutilCommand('cp', args)
  if exit_code != 0:
    raise dp_exceptions.FileUploadError(
        "Failed to upload files ['{0}'] to '{1}' using gsutil.".format(
            "', '".join(files), destination))


def GetBucket(bucket, storage_client=None):
  """Gets a bucket if it exists.

  Args:
    bucket: The bucket name.
    storage_client: Storage client instance.

  Returns:
    A bucket message, or None if it doesn't exist.
  """
  client = storage_client or storage_api.StorageClient()

  try:
    return client.GetBucket(bucket)
  except storage_api.BucketNotFoundError:
    return None


def CreateBucketIfNotExists(bucket, region, storage_client=None, project=None):
  """Creates a bucket.

  Creates a bucket in the specified region. If the region is None, the bucket
  will be created in global region.

  Args:
    bucket: Name of bucket to create.
    region: Region to create bucket in.
    storage_client: Storage client instance.
    project: The project to create the bucket in. If None, current Cloud SDK
    project is used.
  """
  client = storage_client or storage_api.StorageClient()
  client.CreateBucketIfNotExists(bucket, location=region, project=project)


def ReadObject(object_url, storage_client=None):
  """Reads an object's content from GCS.

  Args:
    object_url: The URL of the object to be read. Must have "gs://" prefix.
    storage_client: Storage api client used to read files from gcs.

  Raises:
    ObjectReadError:
      If the read of GCS object is not successful.

  Returns:
    A str for the content of the GCS object.
  """
  client = storage_client or storage_api.StorageClient()
  object_ref = storage_util.ObjectReference.FromUrl(object_url)
  try:
    bytes_io = client.ReadObject(object_ref)
    wrapper = io.TextIOWrapper(bytes_io, encoding='utf-8')
    return wrapper.read()
  except exceptions.BadFileException:
    raise dp_exceptions.ObjectReadError(
        "Failed to read file '{0}'.".format(object_url))


def GetObjectRef(path, messages):
  """Build an Object proto message from a GCS path."""
  resource = resources.REGISTRY.ParseStorageURL(path)
  return messages.Object(bucket=resource.bucket, name=resource.object)


class StorageClient(object):
  """Micro-client for accessing GCS."""

  # TODO(b/36050236): Add application-id.

  def __init__(self):
    self.client = core_apis.GetClientInstance('storage', 'v1')
    self.messages = core_apis.GetMessagesModule('storage', 'v1')

  def _GetObject(self, object_ref, download=None):
    request = self.messages.StorageObjectsGetRequest(
        bucket=object_ref.bucket, object=object_ref.name)
    try:
      return self.client.objects.Get(request=request, download=download)
    except apitools_exceptions.HttpNotFoundError:
      # TODO(b/36052479): Clean up error handling. Handle 403s.
      return None

  def GetObject(self, object_ref):
    """Get the object metadata of a GCS object.

    Args:
      object_ref: A proto message of the object to fetch. Only the bucket and
        name need be set.

    Raises:
      HttpError:
        If the responses status is not 2xx or 404.

    Returns:
      The object if it exists otherwise None.
    """
    return self._GetObject(object_ref)

  def BuildObjectStream(self, stream, object_ref):
    """Build an apitools Download from a stream and a GCS object reference.

    Note: This will always succeed, but HttpErrors with downloading will be
      raised when the download's methods are called.

    Args:
      stream: An Stream-like object that implements write(<string>) to write
        into.
      object_ref: A proto message of the object to fetch. Only the bucket and
        name need be set.

    Returns:
      The download.
    """
    download = transfer.Download.FromStream(
        stream, total_size=object_ref.size, auto_transfer=False)
    self._GetObject(object_ref, download=download)
    return download


class StorageObjectSeriesStream(object):
  """I/O Stream-like class for communicating via a sequence of GCS objects."""

  def __init__(self, path, storage_client=None):
    """Construct a StorageObjectSeriesStream for a specific gcs path.

    Args:
      path: A GCS object prefix which will be the base of the objects used to
          communicate across the channel.
      storage_client: a StorageClient for accessing GCS.

    Returns:
      The constructed stream.
    """
    self._base_path = path
    self._gcs = storage_client or StorageClient()
    self._open = True

    # Index of current object in series.
    self._current_object_index = 0

    # Current position in bytes in the current file.
    self._current_object_pos = 0

  @property
  def open(self):
    """Whether the stream is open."""
    return self._open

  def Close(self):
    """Close the stream."""
    self._open = False

  def _AssertOpen(self):
    if not self.open:
      raise ValueError('I/O operation on closed stream.')

  def _GetObject(self, i):
    """Get the ith object in the series."""
    path = '{0}.{1:09d}'.format(self._base_path, i)
    return self._gcs.GetObject(GetObjectRef(path, self._gcs.messages))

  def ReadIntoWritable(self, writable, n=sys.maxsize):
    """Read from this stream into a writable.

    Reads at most n bytes, or until it sees there is not a next object in the
    series. This will block for the duration of each object's download,
    and possibly indefinitely if new objects are being added to the channel
    frequently enough.

    Args:
      writable: The stream-like object that implements write(<string>) to
          write into.
      n: A maximum number of bytes to read. Defaults to sys.maxsize
        (usually ~4 GB).

    Raises:
      ValueError: If the stream is closed or objects in the series are
        detected to shrink.

    Returns:
      The number of bytes read.
    """
    self._AssertOpen()
    bytes_read = 0
    object_info = None
    max_bytes_to_read = n
    while bytes_read < max_bytes_to_read:
      # Cache away next object first.
      next_object_info = self._GetObject(self._current_object_index + 1)

      # If next object exists always fetch current object to get final size.
      if not object_info or next_object_info:
        try:
          object_info = self._GetObject(self._current_object_index)
        except apitools_exceptions.HttpError as error:
          log.warning('Failed to fetch GCS output:\n%s', error)
          break
        if not object_info:
          # Nothing to read yet.
          break

      new_bytes_available = object_info.size - self._current_object_pos

      if new_bytes_available < 0:
        raise ValueError('Object [{0}] shrunk.'.format(object_info.name))

      if object_info.size == 0:
        # There are no more objects to read
        self.Close()
        break

      bytes_left_to_read = max_bytes_to_read - bytes_read
      new_bytes_to_read = min(bytes_left_to_read, new_bytes_available)

      if new_bytes_to_read > 0:
        # Download range.
        download = self._gcs.BuildObjectStream(writable, object_info)
        download.GetRange(
            self._current_object_pos,
            self._current_object_pos + new_bytes_to_read - 1)
        self._current_object_pos += new_bytes_to_read
        bytes_read += new_bytes_to_read

      # Correct since we checked for next object before getting current
      # object's size.
      object_finished = (
          next_object_info and self._current_object_pos == object_info.size)

      if object_finished:
        object_info = next_object_info
        self._current_object_index += 1
        self._current_object_pos = 0
        continue
      else:
        # That is all there is to read at this time.
        break

    return bytes_read
