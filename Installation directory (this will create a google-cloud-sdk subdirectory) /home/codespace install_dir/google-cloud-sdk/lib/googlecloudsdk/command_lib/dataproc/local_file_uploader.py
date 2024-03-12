# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Helper class for uploading user files to GCS bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.core.console import console_io
import six


def Upload(bucket, files):
  """Uploads user local files to the given GCS bucket.

  Uploads files if they are local.

  The function will prompt users to enter a region to create the bucket if the
  bucket doesn't exist.

  Args:
    bucket: The destination GCS bucket name.
    files: A dictionary of lists of files to upload. Field name of the lists
    won't cause any behavior difference, and the structure will be kept in the
    return value.

  Returns:
    A dictionary of lists of uri of the files. The structure is the same as the
    input files.

  Example:
    Upload('my-bucket', {'jar':['my-jar.jar']}
    > {'jar':['gs://my-bucket/dependencies/my-jar.jar']}
  """
  bucket = _ParseBucketName(bucket)

  result_files = {}

  destination = _FormDestinationUri(bucket)

  # Flag for creating bucket. Mark False after first call to create bucket.
  need_create_bucket = True

  for field, uris in files.items():
    result_files[field] = []
    # Aggregate a list of files that need to be upload.
    need_upload = []
    for uri in uris:
      if _IsLocal(uri):
        # Get reference-able file path. This should be sufficient in most cases.
        expanded_uri = os.path.expandvars(os.path.expanduser(uri))
        need_upload.append(expanded_uri)
        result_files[field].append(_FormFileDestinationUri(
            destination, expanded_uri))
      else:
        # Don't change anything if it is not a local file.
        result_files[field].append(uri)

    if need_upload:
      if need_create_bucket:
        need_create_bucket = False
        _CreateBucketIfNotExists(bucket)
      storage_helpers.Upload(need_upload, destination)

  return result_files


def HasLocalFiles(files):
  """Determines whether files argument has local files.

  Args:
    files: A dictionary of lists of files to check.

  Returns:
    True if at least one of the files is local.

  Example:
    GetLocalFiles({'jar':['my-jar.jar', gs://my-bucket/my-gcs-jar.jar]}) -> True
  """

  for _, uris in files.items():
    for uri in uris:
      if _IsLocal(uri):
        return True

  return False


def _CreateBucketIfNotExists(bucket):
  """Creates a Cloud Storage bucket if it doesn't exist."""
  if storage_helpers.GetBucket(bucket):
    return

  # Ask user to enter a region to create the bucket.
  region = console_io.PromptResponse(
      message=('The bucket [{}] doesn\'t exist. Please enter a '
               'Cloud Storage region to create the bucket (leave empty to '
               'create in "global" region):'.format(bucket)))

  storage_helpers.CreateBucketIfNotExists(bucket, region)


def _ParseBucketName(name):
  """Normalizes bucket name.

  Normalizes bucket name. If it starts with gs://, remove it.
  Api_lib's function doesn't like the gs prefix.

  Args:
    name: gs bucket name string.

  Returns:
    A name string without 'gs://' prefix.
  """
  gs = 'gs://'
  if name.startswith(gs):
    return name[len(gs):]
  return name


def _IsLocal(uri):
  """Checks if a given uri represent a local file."""
  drive, _ = os.path.splitdrive(uri)
  parsed_uri = six.moves.urllib.parse.urlsplit(uri, allow_fragments=False)
  return drive or not parsed_uri.scheme


def _FormDestinationUri(bucket):
  """Forms destination bucket uri."""
  return 'gs://{}/dependencies'.format(bucket)


def _FormFileDestinationUri(destination, uri):
  """Forms uri representing uploaded file."""
  # Mimic the uri logic in storage_helpers.
  return os.path.join(destination, os.path.basename(uri))
