# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Common utility functions for Composer environment storage commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os.path
import posixpath
import re

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import transfer

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
import six


BUCKET_MISSING_MSG = 'Could not retrieve Cloud Storage bucket for environment.'


def WarnIfWildcardIsPresent(path, flag_name):
  """Logs deprecation warning if gsutil wildcards are in args."""
  if path and ('*' in path or '?' in path or re.search(r'\[.*\]', path)):
    log.warning('Use of gsutil wildcards is no longer supported in {0}. '
                'Set the storage/use_gsutil property to get the old behavior '
                'back temporarily. However, this property will eventually be '
                'removed.'.format(flag_name))


# NOTE: Only support 2 paths instead of *args so the gsutil_path doesn't get
# hidden in **kwargs.
def _JoinPaths(path1, path2, gsutil_path=False):
  """Joins paths using the appropriate separator for local or gsutil."""
  if gsutil_path:
    return posixpath.join(path1, path2)
  else:
    return os.path.join(path1, path2)


def List(env_ref, gcs_subdir, release_track=base.ReleaseTrack.GA):
  """Lists all resources in one folder of bucket.

  Args:
    env_ref: googlecloudsdk.core.resources.Resource, Resource representing
        the Environment whose corresponding bucket to list.
    gcs_subdir: str, subdir of the Cloud Storage bucket which to list
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.

  Returns:
    list of Objects inside subdirectory of Cloud Storage bucket for environment

  Raises:
    command_util.Error: if the storage bucket could not be retrieved
  """
  bucket_ref = _GetStorageBucket(env_ref, release_track=release_track)
  storage_client = storage_api.StorageClient()
  return storage_client.ListBucket(bucket_ref, prefix=gcs_subdir + '/')


def Import(env_ref, source, destination, release_track=base.ReleaseTrack.GA):
  """Imports files and directories into a bucket.

  Args:
    env_ref: googlecloudsdk.core.resources.Resource, Resource representing
        the Environment whose bucket into which to import.
    source: str, a path from which to import files into the
        environment's bucket. Directory sources are imported recursively; the
        directory itself will be present in the destination bucket.
        Must contain at least one non-empty value.
    destination: str, subdir of the Cloud Storage bucket into which to import
        `sources`. Must have a single trailing slash but no leading slash. For
        example, 'data/foo/bar/'.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.

  Returns:
    None

  Raises:
    command_util.Error: if the storage bucket could not be retrieved
    command_util.GsutilError: the gsutil command failed
  """
  gcs_bucket = _GetStorageBucket(env_ref, release_track=release_track)

  use_gsutil = properties.VALUES.storage.use_gsutil.GetBool()
  if use_gsutil:
    _ImportGsutil(gcs_bucket, source, destination)
  else:
    _ImportStorageApi(gcs_bucket, source, destination)


def _ImportStorageApi(gcs_bucket, source, destination):
  """Imports files and directories into a bucket."""
  client = storage_api.StorageClient()

  old_source = source
  source = source.rstrip('*')
  # Source ends with an asterisk. This means the user indicates that the source
  # is a directory so we shouldn't bother trying to see if source is an object.
  # This is important because we always have certain subdirs created as objects
  # (e.g. dags/), so if we don't do this check, import/export will just try
  # and copy this empty object.
  object_is_subdir = old_source != source
  if not object_is_subdir:
    # If source is not indicated to be a subdir, then strip the ending slash
    # so the specified directory is present in the destination.
    source = source.rstrip(posixpath.sep)

  source_is_local = not source.startswith('gs://')
  if source_is_local and not os.path.exists(source):
    raise command_util.Error('Source for import does not exist.')

  # Don't include the specified directory as we want that present in the
  # destination bucket.
  source_dirname = _JoinPaths(
      os.path.dirname(source), '', gsutil_path=not source_is_local)
  if source_is_local:
    if os.path.isdir(source):
      file_chooser = gcloudignore.GetFileChooserForDir(source)
      for rel_path in file_chooser.GetIncludedFiles(source):
        file_path = _JoinPaths(source, rel_path)
        if os.path.isdir(file_path):
          continue
        dest_path = _GetDestPath(source_dirname, file_path, destination, False)
        obj_ref = storage_util.ObjectReference.FromBucketRef(gcs_bucket,
                                                             dest_path)
        client.CopyFileToGCS(file_path, obj_ref)
    else:  # Just upload the file.
      dest_path = _GetDestPath(source_dirname, source, destination, False)
      obj_ref = storage_util.ObjectReference.FromBucketRef(gcs_bucket,
                                                           dest_path)
      client.CopyFileToGCS(source, obj_ref)
  else:
    source_ref = storage_util.ObjectReference.FromUrl(source)
    to_import = _GetObjectOrSubdirObjects(
        source_ref, object_is_subdir=object_is_subdir, client=client)
    for obj in to_import:
      dest_object = storage_util.ObjectReference.FromBucketRef(
          gcs_bucket,
          # Use obj.ToUrl() to ensure that the dirname is properly stripped.
          _GetDestPath(source_dirname, obj.ToUrl(), destination, False))
      client.Copy(obj, dest_object)


def _ImportGsutil(gcs_bucket, source, destination):
  """Imports files and directories into a bucket."""
  destination_ref = storage_util.ObjectReference.FromBucketRef(
      gcs_bucket, destination)
  try:
    retval = storage_util.RunGsutilCommand(
        'cp',
        command_args=(['-r', source, destination_ref.ToUrl()]),
        run_concurrent=True,
        out_func=log.out.write,
        err_func=log.err.write)
  except (execution_utils.PermissionError,
          execution_utils.InvalidCommandError) as e:
    raise command_util.GsutilError(six.text_type(e))
  if retval:
    raise command_util.GsutilError('gsutil returned non-zero status code.')


def Export(env_ref, source, destination, release_track=base.ReleaseTrack.GA):
  """Exports files and directories from an environment's Cloud Storage bucket.

  Args:
    env_ref: googlecloudsdk.core.resources.Resource, Resource representing
        the Environment whose bucket from which to export.
    source: str, a  bucket-relative path from which to export files.
        Directory sources are imported recursively; the directory itself will
        be present in the destination bucket. Can also include wildcards.
    destination: str, existing local directory or path to a Cloud Storage
        bucket or directory object to which to export.
        Must have a single trailing slash but no leading slash. For
        example, 'dir/foo/bar/'.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.

  Returns:
    None

  Raises:
    command_util.Error: if the storage bucket could not be retrieved or a
      non-Cloud Storage destination that is not a local directory was provided.
    command_util.GsutilError: the gsutil command failed
  """
  gcs_bucket = _GetStorageBucket(env_ref, release_track=release_track)

  use_gsutil = properties.VALUES.storage.use_gsutil.GetBool()
  if use_gsutil:
    _ExportGsutil(gcs_bucket, source, destination)
  else:
    _ExportStorageApi(gcs_bucket, source, destination)


def _ExportStorageApi(gcs_bucket, source, destination):
  """Exports files and directories from an environment's GCS bucket."""
  old_source = source
  source = source.rstrip('*')
  # Source ends with an asterisk. This means the user indicates that the source
  # is a directory so we shouldn't bother trying to see if source is an object.
  # This is important because we always have certain subdirs created as objects
  # (e.g. dags/), so if we don't do this check, import/export will just try
  # and copy this empty object.
  object_is_subdir = old_source != source

  client = storage_api.StorageClient()
  source_ref = storage_util.ObjectReference.FromBucketRef(gcs_bucket, source)
  dest_is_local = True
  if destination.startswith('gs://'):
    destination = _JoinPaths(
        destination.strip(posixpath.sep), '', gsutil_path=True)
    dest_is_local = False
  elif not os.path.isdir(destination):
    raise command_util.Error('Destination for export must be a directory.')

  source_dirname = _JoinPaths(os.path.dirname(source), '', gsutil_path=True)
  to_export = _GetObjectOrSubdirObjects(
      source_ref, object_is_subdir=object_is_subdir, client=client)
  if dest_is_local:
    for obj in to_export:
      dest_path = _GetDestPath(source_dirname, obj.name, destination, True)
      files.MakeDir(os.path.dirname(dest_path))
      # Command description for export commands says overwriting is default
      # behavior.
      client.CopyFileFromGCS(obj, dest_path, overwrite=True)
  else:
    for obj in to_export:
      dest_object = storage_util.ObjectReference.FromUrl(
          _GetDestPath(source_dirname, obj.name, destination, False))
      client.Copy(obj, dest_object)


def _ExportGsutil(gcs_bucket, source, destination):
  """Exports files and directories from an environment's GCS bucket."""
  source_ref = storage_util.ObjectReference.FromBucketRef(gcs_bucket, source)
  if destination.startswith('gs://'):
    destination = _JoinPaths(
        destination.strip(posixpath.sep), '', gsutil_path=True)
  elif not os.path.isdir(destination):
    raise command_util.Error('Destination for export must be a directory.')

  try:
    retval = storage_util.RunGsutilCommand(
        'cp',
        command_args=['-r', source_ref.ToUrl(), destination],
        run_concurrent=True,
        out_func=log.out.write,
        err_func=log.err.write)
  except (execution_utils.PermissionError,
          execution_utils.InvalidCommandError) as e:
    raise command_util.GsutilError(six.text_type(e))
  if retval:
    raise command_util.GsutilError('gsutil returned non-zero status code.')


def _GetDestPath(source_dirname, source_path, destination, dest_is_local):
  """Get dest path without the dirname of the source dir if present."""
  dest_path_suffix = source_path
  if source_path.startswith(source_dirname):
    dest_path_suffix = source_path[len(source_dirname):]
  # For Windows, replace path separators with the posix path separators.
  if not dest_is_local:
    dest_path_suffix = dest_path_suffix.replace(os.path.sep, posixpath.sep)

  return _JoinPaths(
      destination, dest_path_suffix, gsutil_path=not dest_is_local)


def Delete(env_ref, target, gcs_subdir, release_track=base.ReleaseTrack.GA):
  """Deletes objects in a folder of an environment's bucket.

  gsutil deletes directory marker objects even when told to delete just the
  directory's contents, so we need to check that it exists and create it if it
  doesn't.

  A better alternative will be to use the storage API to list
  objects by prefix and implement deletion ourselves

  Args:
    env_ref: googlecloudsdk.core.resources.Resource, Resource representing
        the Environment in whose corresponding bucket to delete objects.
    target: str, the path within the gcs_subdir directory in the bucket
        to delete. If this is equal to '*', then delete everything in
        gcs_subdir.
    gcs_subdir: str, subdir of the Cloud Storage bucket in which to delete.
        Should not contain slashes, for example "dags".
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.
  """
  gcs_bucket = _GetStorageBucket(env_ref, release_track=release_track)

  use_gsutil = properties.VALUES.storage.use_gsutil.GetBool()
  if use_gsutil:
    _DeleteGsutil(gcs_bucket, target, gcs_subdir)
  else:
    _DeleteStorageApi(gcs_bucket, target, gcs_subdir)
  log.status.Print('Deletion operation succeeded.')

  _EnsureSubdirExists(gcs_bucket, gcs_subdir)


def _DeleteStorageApi(gcs_bucket, target, gcs_subdir):
  """Deletes objects in a folder of an environment's bucket with storage API."""
  client = storage_api.StorageClient()
  # Explicitly only support target = '*' and no other globbing notation.
  # This is because the flag help text explicitly says to give a subdir.
  # Star also has a special meaning and tells the delete function to not try
  # and get the object. This is necessary because subdirs in the GCS buckets
  # are created as objects to ensure they exist.
  delete_all = target == '*'
  # Listing in a bucket uses a prefix match and doesn't support * notation.
  target = '' if delete_all else target
  target_ref = storage_util.ObjectReference.FromBucketRef(
      gcs_bucket, _JoinPaths(gcs_subdir, target, gsutil_path=True))

  to_delete = _GetObjectOrSubdirObjects(
      target_ref, object_is_subdir=delete_all, client=client)
  for obj_ref in to_delete:
    client.DeleteObject(obj_ref)


def _DeleteGsutil(gcs_bucket, target, gcs_subdir):
  """Deletes objects in a folder of an environment's bucket with gsutil."""
  target_ref = storage_util.ObjectReference.FromBucketRef(
      gcs_bucket, _JoinPaths(gcs_subdir, target, gsutil_path=True))
  try:
    retval = storage_util.RunGsutilCommand(
        'rm',
        command_args=(['-r', target_ref.ToUrl()]),
        run_concurrent=True,
        out_func=log.out.write,
        err_func=log.err.write)
  except (execution_utils.PermissionError,
          execution_utils.InvalidCommandError) as e:
    raise command_util.GsutilError(six.text_type(e))
  if retval:
    raise command_util.GsutilError('gsutil returned non-zero status code.')


def _GetObjectOrSubdirObjects(object_ref, object_is_subdir=False, client=None):
  """Gets object_ref or the objects under object_ref is it's a subdir."""
  client = client or storage_api.StorageClient()
  objects = []
  # Check if object_ref referes to an actual object. If it does not exist, we
  # assume the user is specfying a subdirectory.
  target_is_subdir = False
  if not object_is_subdir:
    try:
      client.GetObject(object_ref)
      objects.append(object_ref)
    except apitools_exceptions.HttpNotFoundError:
      target_is_subdir = True

  if target_is_subdir or object_is_subdir:
    target_path = posixpath.join(object_ref.name, '')
    subdir_objects = client.ListBucket(object_ref.bucket_ref, target_path)
    for obj in subdir_objects:
      if object_is_subdir and obj.name == object_ref.name:
        # In this case, object_ref is to be treated as a subdir, so if
        # object_ref happens to also be an object, ignore it.
        continue
      objects.append(
          storage_util.ObjectReference.FromName(object_ref.bucket, obj.name))
  return objects


def _EnsureSubdirExists(bucket_ref, subdir):
  """Checks that a directory marker object exists in the bucket or creates one.

  The directory marker object is needed for subdir listing to not crash
  if the directory is empty.

  Args:
    bucket_ref: googlecloudsk.api_lib.storage.storage_util.BucketReference,
        a reference to the environment's bucket
    subdir: str, the subdirectory to check or recreate. Should not contain
        slashes.
  """
  subdir_name = '{}/'.format(subdir)
  subdir_ref = storage_util.ObjectReference.FromBucketRef(bucket_ref,
                                                          subdir_name)
  storage_client = storage_api.StorageClient()
  try:
    storage_client.GetObject(subdir_ref)
  except apitools_exceptions.HttpNotFoundError:
    # Insert an empty object into the bucket named subdir_name, which will
    # serve as an empty directory marker.
    insert_req = storage_client.messages.StorageObjectsInsertRequest(
        bucket=bucket_ref.bucket,
        name=subdir_name)
    upload = transfer.Upload.FromStream(
        io.BytesIO(), 'application/octet-stream')
    try:
      storage_client.client.objects.Insert(insert_req, upload=upload)
    except apitools_exceptions.HttpError:
      raise command_util.Error(
          'Error re-creating empty {}/ directory most likely due to lack of '
          'permissions.'.format(subdir))
  except apitools_exceptions.HttpForbiddenError:
    raise command_util.Error(
        'Error checking directory {}/ marker object exists due to lack of '
        'permissions.'.format(subdir))


def _GetStorageBucket(env_ref, release_track=base.ReleaseTrack.GA):
  env = environments_api_util.Get(env_ref, release_track=release_track)
  if not env.config.dagGcsPrefix:
    raise command_util.Error(BUCKET_MISSING_MSG)
  try:
    gcs_dag_dir = storage_util.ObjectReference.FromUrl(env.config.dagGcsPrefix)
  except (storage_util.InvalidObjectNameError, ValueError):
    raise command_util.Error(BUCKET_MISSING_MSG)
  return gcs_dag_dir.bucket_ref
