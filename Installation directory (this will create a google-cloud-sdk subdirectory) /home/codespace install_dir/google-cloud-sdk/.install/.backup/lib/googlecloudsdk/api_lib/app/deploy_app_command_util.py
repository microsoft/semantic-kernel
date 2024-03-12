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

"""Utility methods used by the deploy_app command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import hashlib
import os

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.app import metric_names
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import times
from googlecloudsdk.third_party.appengine.tools import context_util
from six.moves import map  # pylint: disable=redefined-builtin


_DEFAULT_NUM_THREADS = 8

# TTL expiry margin, to compensate for incorrect local time and timezone,
# as well as deployment time.
_TTL_MARGIN = datetime.timedelta(1)


class LargeFileError(core_exceptions.Error):

  def __init__(self, path, size, max_size):
    super(LargeFileError, self).__init__(
        ('Cannot upload file [{path}], which has size [{size}] (greater than '
         'maximum allowed size of [{max_size}]). Please delete the file or add '
         'to the skip_files entry in your application .yaml file and try '
         'again.'.format(path=path, size=size, max_size=max_size)))


class MultiError(core_exceptions.Error):

  def __init__(self, operation_description, errors):
    if len(errors) > 1:
      msg = 'Multiple errors occurred {0}\n'.format(operation_description)
    else:
      msg = 'An error occurred {0}\n'.format(operation_description)
    errors_string = '\n\n'.join(map(str, errors))
    super(core_exceptions.Error, self).__init__(msg + errors_string)
    self.errors = errors


def _BuildDeploymentManifest(upload_dir, source_files, bucket_ref, tmp_dir):
  """Builds a deployment manifest for use with the App Engine Admin API.

  Args:
    upload_dir: str, path to the service's upload directory
    source_files: [str], relative paths to upload.
    bucket_ref: The reference to the bucket files will be placed in.
    tmp_dir: A temp directory for storing generated files (currently just source
        context files).
  Returns:
    A deployment manifest (dict) for use with the Admin API.
  """
  manifest = {}
  bucket_url = 'https://storage.googleapis.com/{0}'.format(bucket_ref.bucket)

  # Normal application files.
  for rel_path in source_files:
    full_path = os.path.join(upload_dir, rel_path)
    sha1_hash = file_utils.Checksum.HashSingleFile(full_path,
                                                   algorithm=hashlib.sha1)
    manifest_path = '/'.join([bucket_url, sha1_hash])
    manifest[_FormatForManifest(rel_path)] = {
        'sourceUrl': manifest_path,
        'sha1Sum': sha1_hash
    }

  # Source context files. These are temporary files which indicate the current
  # state of the source repository (git, cloud repo, etc.)
  context_files = context_util.CreateContextFiles(
      tmp_dir, None, source_dir=upload_dir)
  for context_file in context_files:
    rel_path = os.path.basename(context_file)
    if rel_path in manifest:
      # The source context file was explicitly provided by the user.
      log.debug('Source context already exists. Using the existing file.')
      continue
    else:
      sha1_hash = file_utils.Checksum.HashSingleFile(context_file,
                                                     algorithm=hashlib.sha1)
      manifest_path = '/'.join([bucket_url, sha1_hash])
      manifest[_FormatForManifest(rel_path)] = {
          'sourceUrl': manifest_path,
          'sha1Sum': sha1_hash,
      }
  return manifest


def _GetLifecycleDeletePolicy(storage_client, bucket_ref):
  """Get the TTL of objects in days as specified by the lifecycle policy.

  Only "delete by age" policies are accounted for.

  Args:
    storage_client: storage_api.StorageClient, API client wrapper.
    bucket_ref: The GCS bucket reference.

  Returns:
    datetime.timedelta, TTL of objects in days, or None if no deletion
    policy on the bucket.
  """
  try:
    bucket = storage_client.client.buckets.Get(
        request=storage_client.messages.StorageBucketsGetRequest(
            bucket=bucket_ref.bucket),
        global_params=storage_client.messages.StandardQueryParameters(
            fields='lifecycle'))
  except apitools_exceptions.HttpForbiddenError:
    return None
  if not bucket.lifecycle:
    return None
  rules = bucket.lifecycle.rule
  ages = [
      rule.condition.age for rule in rules if rule.condition.age is not None and
      rule.condition.age >= 0 and rule.action.type == 'Delete'
  ]
  return datetime.timedelta(min(ages)) if ages else None


def _IsTTLSafe(ttl, obj):
  """Determines whether a GCS object is close to end-of-life.

  In order to reduce false negative rate (objects that are close to deletion but
  aren't marked as such) the returned filter is forward-adjusted with
  _TTL_MARGIN.

  Args:
    ttl: datetime.timedelta, TTL of objects, or None if no TTL.
    obj: storage object to check.

  Returns:
    True if the ojbect is safe or False if it is approaching end of life.
  """
  if ttl is None:
    return True
  now = times.Now(times.UTC)
  delta = ttl - _TTL_MARGIN
  return (now - obj.timeCreated) <= delta


def _BuildFileUploadMap(manifest, source_dir, bucket_ref, tmp_dir,
                        max_file_size):
  """Builds a map of files to upload, indexed by their hash.

  This skips already-uploaded files.

  Args:
    manifest: A dict containing the deployment manifest for a single service.
    source_dir: The relative source directory of the service.
    bucket_ref: The GCS bucket reference to upload files into.
    tmp_dir: The path to a temporary directory where generated files may be
      stored. If a file in the manifest is not found in the source directory,
      it will be retrieved from this directory instead.
    max_file_size: int, File size limit per individual file or None if no limit.

  Raises:
    LargeFileError: if one of the files to upload exceeds the maximum App Engine
    file size.

  Returns:
    A dict mapping hashes to file paths that should be uploaded.
  """
  files_to_upload = {}
  storage_client = storage_api.StorageClient()
  ttl = _GetLifecycleDeletePolicy(storage_client, bucket_ref)
  existing_items = set(o.name for o in storage_client.ListBucket(bucket_ref)
                       if _IsTTLSafe(ttl, o))
  skipped_size, total_size = 0, 0
  for rel_path in manifest:
    full_path = os.path.join(source_dir, rel_path)
    # For generated files, the relative path is based on the tmp_dir rather
    # than source_dir. If the file is not in the source directory, look in
    # tmp_dir instead.
    if not os.path.exists(encoding.Encode(full_path, encoding='utf-8')):
      full_path = os.path.join(tmp_dir, rel_path)
    # Perform this check when creating the upload map, so we catch too-large
    # files that have already been uploaded
    size = os.path.getsize(encoding.Encode(full_path, encoding='utf-8'))
    if max_file_size and size > max_file_size:
      raise LargeFileError(full_path, size, max_file_size)

    sha1_hash = manifest[rel_path]['sha1Sum']
    total_size += size
    if sha1_hash in existing_items:
      log.debug('Skipping upload of [{f}]'.format(f=rel_path))
      skipped_size += size
    else:
      files_to_upload[sha1_hash] = full_path
    if total_size:
      log.info('Incremental upload skipped {pct}% of data'.format(
          pct=round(100.0 * skipped_size / total_size, 2)))
  return files_to_upload


class FileUploadTask(object):

  def __init__(self, sha1_hash, path, bucket_url):
    self.sha1_hash = sha1_hash
    self.path = path
    self.bucket_url = bucket_url


def _UploadFilesThreads(files_to_upload, bucket_ref):
  """Uploads files to App Engine Cloud Storage bucket using threads.

  Args:
    files_to_upload: dict {str: str}, map of checksum to local path
    bucket_ref: storage_api.BucketReference, the reference to the bucket files
      will be placed in.

  Raises:
    MultiError: if one or more errors occurred during file upload.
  """
  num_threads = (properties.VALUES.app.num_file_upload_threads.GetInt() or
                 storage_parallel.DEFAULT_NUM_THREADS)
  tasks = []
  # Have to sort files because the test framework requires a known order for
  # mocked API calls.
  for sha1_hash, path in sorted(files_to_upload.items()):
    dest_obj_ref = storage_util.ObjectReference.FromBucketRef(bucket_ref,
                                                              sha1_hash)
    task = storage_parallel.FileUploadTask(path, dest_obj_ref)
    tasks.append(task)
  storage_parallel.UploadFiles(tasks, num_threads=num_threads,
                               show_progress_bar=True)


def CopyFilesToCodeBucket(upload_dir, source_files,
                          bucket_ref, max_file_size=None):
  """Copies application files to the Google Cloud Storage code bucket.

  Use the Cloud Storage API using threads.

  Consider the following original structure:
    app/
      main.py
      tools/
        foo.py

   Assume main.py has SHA1 hash 123 and foo.py has SHA1 hash 456. The resultant
   GCS bucket will look like this:
     gs://$BUCKET/
       123
       456

   The resulting App Engine API manifest will be:
     {
       "app/main.py": {
         "sourceUrl": "https://storage.googleapis.com/staging-bucket/123",
         "sha1Sum": "123"
       },
       "app/tools/foo.py": {
         "sourceUrl": "https://storage.googleapis.com/staging-bucket/456",
         "sha1Sum": "456"
       }
     }

    A 'list' call of the bucket is made at the start, and files that hash to
    values already present in the bucket will not be uploaded again.

  Args:
    upload_dir: str, path to the service's upload directory
    source_files: [str], relative paths to upload.
    bucket_ref: The reference to the bucket files will be placed in.
    max_file_size: int, File size limit per individual file or None if no limit.

  Returns:
    A dictionary representing the manifest.
  """
  metrics.CustomTimedEvent(metric_names.COPY_APP_FILES_START)
  # Collect a list of files to upload, indexed by the SHA so uploads are
  # deduplicated.
  with file_utils.TemporaryDirectory() as tmp_dir:
    manifest = _BuildDeploymentManifest(
        upload_dir, source_files, bucket_ref, tmp_dir)
    files_to_upload = _BuildFileUploadMap(
        manifest, upload_dir, bucket_ref, tmp_dir, max_file_size)
    _UploadFilesThreads(files_to_upload, bucket_ref)
  log.status.Print('File upload done.')
  log.info('Manifest: [{0}]'.format(manifest))
  metrics.CustomTimedEvent(metric_names.COPY_APP_FILES)
  return manifest


def _FormatForManifest(filename):
  """Reformat a filename for the deployment manifest if it is Windows format."""
  if os.path.sep == '\\':
    return filename.replace('\\', '/')
  return filename
