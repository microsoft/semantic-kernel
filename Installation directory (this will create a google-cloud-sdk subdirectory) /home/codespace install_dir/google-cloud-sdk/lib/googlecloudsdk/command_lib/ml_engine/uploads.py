# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Common ML file upload logic."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import os

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files as file_utils
import six
from six.moves import zip


# For ease of mocking in tests without messing up core Python functionality
_PATH_SEP = os.path.sep


class MissingStagingBucketException(Exception):
  """Indicates that a staging bucket was not provided with a local path.

  It doesn't inherit from core.exceptions.Error because it should be caught and
  re-raised at the call site with an actionable message.
  """


class BadDirectoryError(exceptions.Error):
  """Indicates that a provided directory for upload was empty."""


def UploadFiles(upload_pairs, bucket_ref, gs_prefix=None):
  """Uploads files at the local path to a specifically prefixed location.

  The prefix is 'cloudmldist/<current timestamp>'.

  Args:
    upload_pairs: [(str, str)]. Pairs of absolute paths to local files to upload
      and corresponding path in Cloud Storage (that goes after the prefix). For
      example, ('/path/foo', 'bar') will upload '/path/foo' to '<prefix>/bar' in
      Cloud Storage.
    bucket_ref: storage_util.BucketReference.
      Files will be uploaded to this bucket.
    gs_prefix: str. Prefix to the GCS Path where files will be uploaded.
  Returns:
    [str]. A list of fully qualified gcs paths for the uploaded files, in the
      same order they were provided.
  """

  checksum = file_utils.Checksum(algorithm=hashlib.sha256)
  for local_path, _ in upload_pairs:
    checksum.AddFileContents(local_path)

  if gs_prefix is not None:
    gs_prefix = '/'.join([gs_prefix, checksum.HexDigest()])
  else:
    gs_prefix = checksum.HexDigest()

  storage_client = storage_api.StorageClient()
  dests = []
  for local_path, uploaded_path in upload_pairs:
    obj_ref = storage_util.ObjectReference.FromBucketRef(
        bucket_ref, '/'.join([gs_prefix, uploaded_path]))
    obj = storage_client.CopyFileToGCS(local_path, obj_ref)
    dests.append('/'.join(['gs:/', obj.bucket, obj.name]))
  return dests


def _GetFilesRelative(root):
  """Return all the descendents of root, relative to its path.

  For instance, given the following directory structure

      /path/to/root/a
      /path/to/root/a/b
      /path/to/root/c

  This function would return `['a', 'a/b', 'c']`.

  Args:
    root: str, the path to list descendents of.

  Returns:
    list of str, the paths in the given directory.
  """
  paths = []
  for dirpath, _, filenames in os.walk(six.text_type(root)):
    for filename in filenames:
      abs_path = os.path.join(dirpath, filename)
      paths.append(os.path.relpath(abs_path, start=root))
  return paths


def UploadDirectoryIfNecessary(path, staging_bucket=None, gs_prefix=None):
  """Uploads path to Cloud Storage if it isn't already there.

  Translates local file system paths to Cloud Storage-style paths (i.e. using
  the Unix path separator '/').

  Args:
    path: str, the path to the directory. Can be a Cloud Storage ("gs://") path
      or a local filesystem path (no protocol).
    staging_bucket: storage_util.BucketReference or None. If the path is local,
      the bucket to which it should be uploaded.
    gs_prefix: str, prefix for the directory within the staging bucket.

  Returns:
    str, a Cloud Storage path where the directory has been uploaded (possibly
      prior to the execution of this function).

  Raises:
    MissingStagingBucketException: if `path` is a local path, but staging_bucket
      isn't found.
    BadDirectoryError: if the given directory couldn't be found or is empty.
  """
  if path.startswith('gs://'):
    # The "directory" is already in Cloud Storage, so nothing needs to be done
    return path

  if staging_bucket is None:
    # If the directory is local, a staging bucket must be provided
    raise MissingStagingBucketException(
        'The path provided was local, but no staging bucket for upload '
        'was provided.')

  if not os.path.isdir(path):
    raise BadDirectoryError('[{}] is not a valid directory.'.format(path))

  files = _GetFilesRelative(path)
  # We want to upload files using '/' as a virtual file separator, since that's
  # what Cloud Storage uses.
  dests = [f.replace(_PATH_SEP, '/') for f in files]
  # We put `path` back in, so that UploadFiles can actually find them.
  full_files = [_PATH_SEP.join([path, f]) for f in files]

  uploaded_paths = UploadFiles(list(zip(full_files, dests)),
                               staging_bucket,
                               gs_prefix=gs_prefix)

  if not uploaded_paths:
    raise BadDirectoryError(
        'Cannot upload contents of directory [{}] to Google Cloud Storage; '
        'directory has no files.'.format(path))
  # Get the prefix used by removing the part that we specified from the output.
  # Depends on the order of the result of UploadFiles.
  return uploaded_paths[0][:-len(dests[0])]
