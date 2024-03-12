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

"""Utilities for interacting with Google Cloud Storage.

This makes use of both the Cloud Storage API as well as the gsutil command-line
tool. We use the command-line tool for syncing the contents of buckets as well
as listing the contents. We use the API for checking ACLs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import mimetypes
import os

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import list_pager
from apitools.base.py import transfer

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import exceptions as http_exc
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import exceptions as core_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import transports
from googlecloudsdk.core.util import scaled_integer

import six


class Error(core_exc.Error):
  """Base exception for storage API module."""


class BucketNotFoundError(Error):
  """Error raised when the bucket specified does not exist."""


class ListBucketError(Error):
  """Error raised when there are problems listing the contents of a bucket."""


class UploadError(Error):
  """Error raised when there are problems uploading files."""


class BucketInWrongProjectError(Error):
  """Error raised when a bucket exists in a project the user doesn't own.

  Specifically, this applies when a command creates a bucket if it doesn't
  exist, or returns the existing bucket otherwise. If the bucket exists but is
  owned by a different project, it could belong to a malicious user squatting on
  the bucket name.
  """


def _GetMimetype(local_path):
  mime_type, _ = mimetypes.guess_type(local_path)
  return mime_type or 'application/octet-stream'


def _GetFileSize(local_path):
  try:
    return os.path.getsize(six.ensure_str(local_path))
  except os.error:
    raise exceptions.BadFileException('[{0}] not found or not accessible'
                                      .format(local_path))


class StorageClient(object):
  """Client for Google Cloud Storage API."""

  def __init__(self, client=None, messages=None):
    self.client = client or storage_util.GetClient()
    self.messages = messages or storage_util.GetMessages()

  def _GetChunkSize(self):
    """Returns the property defined chunksize corrected for server granularity.

    Chunk size for GCS must be a multiple of 256 KiB. This functions rounds up
    the property defined chunk size to the nearest chunk size interval.
    """
    gcs_chunk_granularity = 256 * 1024  # 256 KiB
    chunksize = scaled_integer.ParseInteger(
        properties.VALUES.storage.upload_chunk_size.Get())
    if chunksize == 0:
      chunksize = None  # Use apitools default (1048576 B)
    elif chunksize % gcs_chunk_granularity != 0:
      chunksize += gcs_chunk_granularity - (chunksize % gcs_chunk_granularity)
    return chunksize

  def ListBuckets(self, project):
    """List the buckets associated with the given project."""
    request = self.messages.StorageBucketsListRequest(project=project)
    for b in list_pager.YieldFromList(self.client.buckets,
                                      request, batch_size=None):
      yield b

  def Copy(self, src, dst):
    """Copy one GCS object to another.

    Args:
      src: Resource, the storage object resource to be copied from.
      dst: Resource, the storage object resource to be copied to.

    Returns:
      Object, the storage object that was copied to.
    """
    return self.client.objects.Copy(
        self.messages.StorageObjectsCopyRequest(
            sourceBucket=src.bucket,
            sourceObject=src.object,
            destinationBucket=dst.bucket,
            destinationObject=dst.object,
        ))

  def Rewrite(self, src, dst):
    """Rewrite one GCS object to another.

    This method has the same result as the Copy method, but can handle moving
    large objects that may potentially timeout a Copy request.

    Args:
      src: Resource, the storage object resource to be copied from.
      dst: Resource, the storage object resource to be copied to.

    Returns:
      Object, the storage object that was copied to.
    """
    rewrite_token = None
    while True:
      resp = self.client.objects.Rewrite(
          self.messages.StorageObjectsRewriteRequest(
              sourceBucket=src.bucket,
              sourceObject=src.object,
              destinationBucket=dst.bucket,
              destinationObject=dst.object,
              rewriteToken=rewrite_token,
          ))
      if resp.done:
        return resp.resource
      rewrite_token = resp.rewriteToken

  def GetObject(self, object_ref):
    """Gets an object from the given Cloud Storage bucket.

    Args:
      object_ref: storage_util.ObjectReference, The user-specified bucket to
        download from.

    Returns:
      Object: a StorageV1 Object message with details about the object.
    """
    return self.client.objects.Get(self.messages.StorageObjectsGetRequest(
        bucket=object_ref.bucket,
        object=object_ref.object))

  def CopyFileToGCS(self, local_path, target_obj_ref):
    """Upload a file to the GCS results bucket using the storage API.

    Args:
      local_path: str, the path of the file to upload. File must be on the local
        filesystem.
      target_obj_ref: storage_util.ObjectReference, the path of the file on GCS.

    Returns:
      Object, the storage object that was copied to.

    Raises:
      BucketNotFoundError if the user-specified bucket does not exist.
      UploadError if the file upload is not successful.
      exceptions.BadFileException if the uploaded file size does not match the
          size of the local file.
    """
    file_size = _GetFileSize(local_path)
    src_obj = self.messages.Object(size=file_size)
    mime_type = _GetMimetype(local_path)

    chunksize = self._GetChunkSize()
    upload = transfer.Upload.FromFile(
        six.ensure_str(local_path), mime_type=mime_type, chunksize=chunksize)
    insert_req = self.messages.StorageObjectsInsertRequest(
        bucket=target_obj_ref.bucket,
        name=target_obj_ref.object,
        object=src_obj)

    gsc_path = '{bucket}/{target_path}'.format(
        bucket=target_obj_ref.bucket, target_path=target_obj_ref.object,
    )

    log.info('Uploading [{local_file}] to [{gcs}]'.format(local_file=local_path,
                                                          gcs=gsc_path))
    try:
      response = self.client.objects.Insert(insert_req, upload=upload)
    except api_exceptions.HttpNotFoundError:
      raise BucketNotFoundError(
          'Could not upload file: [{bucket}] bucket does not exist.'
          .format(bucket=target_obj_ref.bucket))
    except api_exceptions.HttpError as err:
      log.debug('Could not upload file [{local_file}] to [{gcs}]: {e}'.format(
          local_file=local_path, gcs=gsc_path,
          e=http_exc.HttpException(err)))
      raise UploadError(
          '{code} Could not upload file [{local_file}] to [{gcs}]: {message}'
          .format(code=err.status_code, local_file=local_path, gcs=gsc_path,
                  message=http_exc.HttpException(
                      err, error_format='{status_message}')))
    finally:
      # If the upload fails with an error, apitools (for whatever reason)
      # doesn't close the file object, so we have to call this ourselves to
      # force it to happen.
      upload.stream.close()

    if response.size != file_size:
      log.debug('Response size: {0} bytes, but local file is {1} bytes.'.format(
          response.size, file_size))
      raise exceptions.BadFileException(
          'Cloud storage upload failure. Uploaded file does not match local '
          'file: {0}. Please retry.'.format(local_path))
    return response

  def CopyFileFromGCS(self, source_obj_ref, local_path, overwrite=False):
    """Download a file from the given Cloud Storage bucket.

    Args:
      source_obj_ref: storage_util.ObjectReference, the path of the file on GCS
        to download.
      local_path: str, the path of the file to download to. Path must be on the
        local filesystem.
      overwrite: bool, whether or not to overwrite local_path if it already
        exists.

    Raises:
      BadFileException if the file download is not successful.
    """
    chunksize = self._GetChunkSize()
    download = transfer.Download.FromFile(
        local_path, chunksize=chunksize, overwrite=overwrite)
    download.bytes_http = transports.GetApitoolsTransport(
        response_encoding=None)
    get_req = self.messages.StorageObjectsGetRequest(
        bucket=source_obj_ref.bucket,
        object=source_obj_ref.object)

    gsc_path = '{bucket}/{object_path}'.format(
        bucket=source_obj_ref.bucket, object_path=source_obj_ref.object,
    )

    log.info('Downloading [{gcs}] to [{local_file}]'.format(
        local_file=local_path, gcs=gsc_path))
    try:
      self.client.objects.Get(get_req, download=download)
      # When there's a download, Get() returns None so we Get() again to check
      # the file size.
      response = self.client.objects.Get(get_req)
    except api_exceptions.HttpError as err:
      raise exceptions.BadFileException(
          'Could not copy [{gcs}] to [{local_file}]. Please retry: {err}'
          .format(local_file=local_path, gcs=gsc_path,
                  err=http_exc.HttpException(err)))
    finally:
      # Close the stream to release the file handle so we can check its contents
      download.stream.close()

    file_size = _GetFileSize(local_path)
    if response.size != file_size:
      log.debug('Download size: {0} bytes, but expected size is {1} '
                'bytes.'.format(file_size, response.size))
      raise exceptions.BadFileException(
          'Cloud Storage download failure. Downloaded file [{0}] does not '
          'match Cloud Storage object. Please retry.'.format(local_path))

  def ReadObject(self, object_ref):
    """Read a file from the given Cloud Storage bucket.

    Args:
      object_ref: storage_util.ObjectReference, The object to read from.

    Raises:
      BadFileException if the file read is not successful.

    Returns:
      file-like object containing the data read.
    """
    data = io.BytesIO()
    chunksize = self._GetChunkSize()
    download = transfer.Download.FromStream(data, chunksize=chunksize)
    download.bytes_http = transports.GetApitoolsTransport(
        response_encoding=None)
    get_req = self.messages.StorageObjectsGetRequest(
        bucket=object_ref.bucket,
        object=object_ref.object)

    log.info('Reading [%s]', object_ref)
    try:
      self.client.objects.Get(get_req, download=download)
    except api_exceptions.HttpError as err:
      raise exceptions.BadFileException(
          'Could not read [{object_}]. Please retry: {err}'.format(
              object_=object_ref, err=http_exc.HttpException(err)))

    data.seek(0)
    return data

  def GetBucket(self, bucket, projection=None):
    """Gets a bucket from GCS, if it exists.

    Args:
      bucket: str, The bucket name.
      projection: int, The fields to get as part of this request. This is
        optional and defaults to whatever the server provides.

    Returns:
      Bucket: a StorageV1 Bucket message with details about the bucket.

    Raises:
      BucketNotFoundError if the given bucket does not exist.
    """
    try:
      return self.client.buckets.Get(self.messages.StorageBucketsGetRequest(
          bucket=bucket,
          projection=projection
      ))
    except api_exceptions.HttpNotFoundError:
      # Bucket doesn't exist, we'll try to create it.
      raise BucketNotFoundError('Bucket [{}] does not exist.'.format(bucket))

  def CreateBucketIfNotExists(
      self,
      bucket,
      project=None,
      location=None,
      check_ownership=True,
      enable_uniform_level_access=None,
      cors=None,
  ):
    """Create a bucket if it does not already exist.

    If it already exists and is accessible by the current user, this method
    returns.

    Args:
      bucket: str, The storage bucket to be created.
      project: str, The project to use for the API request. If None, current
        Cloud SDK project is used.
      location: str, The bucket location/region.
      check_ownership: bool, Whether to check that the resulting bucket belongs
        to the given project. DO NOT SET THIS TO FALSE if the bucket name can be
        guessed and claimed ahead of time by another user as it enables a name
        squatting exploit.
      enable_uniform_level_access: bool, to enable uniform bucket level access.
        If None, the iamConfiguration object will not be created in the bucket
        creation request, which means that it will use the default values.
      cors: list, A list of CorsValueListEntry objects. The bucket's
        Cross-Origin Resource Sharing (CORS) configuration. If None, no CORS
        configuration will be set.

    Raises:
      api_exceptions.HttpError: If the bucket is not able to be created or is
        not accessible due to permissions.
      BucketInWrongProjectError: If the bucket already exists in a different
        project. This could belong to a malicious user squatting on the bucket
        name.
    """
    project = project or properties.VALUES.core.project.Get(required=True)

    # Previous iterations of this code always attempted to Insert the bucket
    # and interpreted conflict errors to mean the bucket already existed; this
    # avoids a race condition, but meant that checking bucket existence was
    # subject to a lower-QPS rate limit for bucket creation/deletion. Instead,
    # we do a racy Get-then-Insert which is subject to a higher rate limit, and
    # still have to handle conflict errors in case of a race.
    try:
      self.client.buckets.Get(self.messages.StorageBucketsGetRequest(
          bucket=bucket,
      ))
    except api_exceptions.HttpNotFoundError:
      # Bucket doesn't exist, we'll try to create it.
      storage_buckets_insert_request = (
          self.messages.StorageBucketsInsertRequest(
              project=project,
              bucket=self.messages.Bucket(name=bucket,
                                          location=location)))
      if enable_uniform_level_access is not None:
        storage_buckets_insert_request.bucket.iamConfiguration = (
            self.messages.Bucket.IamConfigurationValue(
                uniformBucketLevelAccess=(
                    self.messages.Bucket.IamConfigurationValue.UniformBucketLevelAccessValue(
                        enabled=enable_uniform_level_access))))
      if cors is not None:
        storage_buckets_insert_request.bucket.cors = cors
      try:
        self.client.buckets.Insert(storage_buckets_insert_request)
      except api_exceptions.HttpConflictError:
        # We lost a race with another process creating the bucket. At least we
        # know the bucket exists. But we must check again whether the
        # newly-created bucket is accessible to us, so we Get it again.
        self.client.buckets.Get(self.messages.StorageBucketsGetRequest(
            bucket=bucket,
        ))
      else:
        # We just created the bucket ourselves; no need to check for ownership.
        return

    if not check_ownership:
      return
    # Check that the bucket is in the user's project to prevent bucket squatting
    # exploit (see b/33046325, b/169171543).
    bucket_list_req = self.messages.StorageBucketsListRequest(
        project=project, prefix=bucket)
    bucket_list = self.client.buckets.List(bucket_list_req)
    if not any(b.id == bucket for b in bucket_list.items):
      raise BucketInWrongProjectError(
          'Unable to create bucket [{}] as it already exists in another '
          'project.'.format(bucket))

  def GetBucketLocationForFile(self, object_path):
    """Returns the location of the bucket for a file.

    Args:
      object_path: str, the path of the file in GCS.

    Returns:
      str, bucket location (region) for given object in GCS.

    Raises:
      BucketNotFoundError if bucket from the object path is not found.
    """

    object_reference = storage_util.ObjectReference.FromUrl(object_path)
    bucket_name = object_reference.bucket
    get_bucket_req = self.messages.StorageBucketsGetRequest(
        bucket=bucket_name)

    try:
      source_bucket = self.client.buckets.Get(get_bucket_req)
      return source_bucket.location
    except api_exceptions.HttpNotFoundError:
      raise BucketNotFoundError(
          'Could not get location for file: [{bucket}] bucket does not exist.'
          .format(bucket=bucket_name))

  def ListBucket(self, bucket_ref, prefix=None):
    """Lists the contents of a cloud storage bucket.

    Args:
      bucket_ref: The reference to the bucket.
      prefix: str, Filter results to those whose names begin with this prefix.

    Yields:
      Object messages.

    Raises:
      BucketNotFoundError if the user-specified bucket does not exist.
      ListBucketError if there was an error listing the bucket.
    """
    request = self.messages.StorageObjectsListRequest(
        bucket=bucket_ref.bucket, prefix=prefix)

    try:
      # batch_size=None gives us the API default
      for obj in list_pager.YieldFromList(self.client.objects,
                                          request, batch_size=None):
        yield obj
    except api_exceptions.HttpNotFoundError:
      raise BucketNotFoundError(
          'Could not list bucket: [{bucket}] bucket does not exist.'
          .format(bucket=bucket_ref.bucket))
    except api_exceptions.HttpError as e:
      log.debug('Could not list bucket [{bucket}]: {e}'.format(
          bucket=bucket_ref.bucket, e=http_exc.HttpException(e)))
      raise ListBucketError(
          '{code} Could not list bucket [{bucket}]: {message}'
          .format(code=e.status_code, bucket=bucket_ref.bucket,
                  message=http_exc.HttpException(
                      e, error_format='{status_message}')))

  def DeleteObject(self, object_ref):
    """Delete the specified object.

    Args:
      object_ref: storage_util.ObjectReference, The object to delete.
    """
    self.client.objects.Delete(self.messages.StorageObjectsDeleteRequest(
        bucket=object_ref.bucket,
        object=object_ref.object))

  def DeleteBucket(self, bucket_ref):
    """Delete the specified bucket.

    Args:
      bucket_ref: storage_util.BucketReference to the bucket of the object
    """
    self.client.buckets.Delete(
        self.messages.StorageBucketsDeleteRequest(bucket=bucket_ref.bucket))

  def GetIamPolicy(self, bucket_ref):
    """Fetch the IAM Policy attached to the specified bucket.

    Args:
      bucket_ref: storage_util.BucketReference to the bucket with the policy.

    Returns:
      The bucket's IAM Policy.
    """
    return self.client.buckets.GetIamPolicy(
        self.messages.StorageBucketsGetIamPolicyRequest(
            bucket=bucket_ref.bucket,
            optionsRequestedPolicyVersion=iam_util
            .MAX_LIBRARY_IAM_SUPPORTED_VERSION))

  def SetIamPolicy(self, bucket_ref, policy):
    """Set the IAM Policy attached to the specified bucket to the given policy.

    If 'policy' has no etag specified, this will BLINDLY OVERWRITE the IAM
    policy!

    Args:
      bucket_ref: storage_util.BucketReference to the bucket.
      policy: The new IAM Policy.

    Returns:
      The new IAM Policy.
    """
    return self.client.buckets.SetIamPolicy(
        self.messages.StorageBucketsSetIamPolicyRequest(
            bucket=bucket_ref.bucket, policy=policy))

  def AddIamPolicyBinding(self, bucket_ref, member, role):
    """Add an IAM policy binding on the specified bucket.

    Does an atomic Read-Modify-Write, adding the member to the role.

    Args:
      bucket_ref: storage_util.BucketReference to the bucket with the policy.
      member: Principal to add to the policy binding.
      role: Role to add to the policy binding.

    Returns:
      The new IAM Policy.
    """
    return self.AddIamPolicyBindings(bucket_ref, [(member, role)])

  def AddIamPolicyBindings(self, bucket_ref, member_roles):
    """Add IAM policy bindings on the specified bucket.

    Does an atomic Read-Modify-Write, adding the member to the role.

    Args:
      bucket_ref: storage_util.BucketReference to the bucket with the policy.
      member_roles: List of 2-tuples in the form [(member, role), ...].

    Returns:
      The new IAM Policy.
    """
    policy = self.GetIamPolicy(bucket_ref)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    policy_was_updated = False
    for member, role in member_roles:
      if iam_util.AddBindingToIamPolicy(
          self.messages.Policy.BindingsValueListEntry, policy, member, role):
        policy_was_updated = True

    if policy_was_updated:
      return self.SetIamPolicy(bucket_ref, policy)

    return policy
