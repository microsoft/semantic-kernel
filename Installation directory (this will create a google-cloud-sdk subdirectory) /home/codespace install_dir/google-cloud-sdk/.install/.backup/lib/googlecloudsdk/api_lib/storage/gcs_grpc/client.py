# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Client for interacting with Google Cloud Storage using gRPC API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage.gcs_grpc import download
from googlecloudsdk.api_lib.storage.gcs_grpc import metadata_util
from googlecloudsdk.api_lib.storage.gcs_grpc import upload
from googlecloudsdk.api_lib.storage.gcs_json import client as gcs_json_client
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.core import exceptions as core_exceptions


class GrpcClientWithJsonFallback(gcs_json_client.JsonClient):
  """Client for Google Cloud Storage API using gRPC with JSON fallback."""

  def __init__(self):
    super(GrpcClientWithJsonFallback, self).__init__()
    self._gapic_client = None

  def _get_gapic_client(self):
    # Not using @property because the side-effect is non-trivial and
    # might not be obvious. Someone might accidentally access the
    # property and end up creating the gapic client.
    # Creating the gapic client before "fork" will lead to a deadlock.
    if self._gapic_client is None:
      self._gapic_client = core_apis.GetGapicClientInstance('storage', 'v2')
    return self._gapic_client

  def compose_objects(
      self,
      source_resources,
      destination_resource,
      request_config,
      original_source_resource=None,
      posix_to_set=None,
  ):
    """See super class."""
    pass

  def copy_object(
      self,
      source_resource,
      destination_resource,
      request_config,
      posix_to_set=None,
      progress_callback=None,
      should_deep_copy_metadata=False,
  ):
    """See super class."""
    pass

  def delete_object(self, object_url, request_config):
    """See super class."""
    pass

  def restore_object(self, url, request_config):
    """See super class."""
    pass

  def bulk_restore_objects(
      self,
      bucket_url,
      object_globs,
      request_config,
      allow_overwrite=False,
      deleted_after_time=None,
      deleted_before_time=None,
  ):
    """See super class."""
    pass

  def download_object(
      self,
      cloud_resource,
      download_stream,
      request_config,
      digesters=None,
      do_not_decompress=False,
      download_strategy=cloud_api.DownloadStrategy.RESUMABLE,
      progress_callback=None,
      start_byte=0,
      end_byte=None,
  ):
    """See super class."""
    if download_util.return_and_report_if_nothing_to_download(
        cloud_resource, progress_callback
    ):
      return None

    if (
        request_config.resource_args is not None
        and request_config.resource_args.decryption_key is not None
    ):
      decryption_key = request_config.resource_args.decryption_key
    else:
      decryption_key = None
    downloader = download.GrpcDownload(
        gapic_client=self._get_gapic_client(),
        cloud_resource=cloud_resource,
        download_stream=download_stream,
        start_byte=start_byte,
        end_byte=end_byte,
        digesters=digesters,
        progress_callback=progress_callback,
        download_strategy=download_strategy,
        decryption_key=decryption_key)
    downloader.run()
    # Unlike JSON, the response message for gRPC does not hold any
    # content-encoding information. Hence, we do not have to return the
    # server encoding here.
    return None

  def upload_object(
      self,
      source_stream,
      destination_resource,
      request_config,
      posix_to_set=None,
      serialization_data=None,
      source_resource=None,
      tracker_callback=None,
      upload_strategy=cloud_api.UploadStrategy.SIMPLE,
  ):
    """See super class."""

    client = self._get_gapic_client()

    source_path = self._get_source_path(source_resource)
    should_gzip_in_flight = gzip_util.should_gzip_in_flight(
        request_config.gzip_settings, source_path)

    if should_gzip_in_flight:
      raise core_exceptions.InternalError(
          'Gzip transport encoding is not supported with GRPC API, please use'
          ' the JSON API instead, changing the storage/preferred_api config'
          ' value to json.'
      )

    if upload_strategy == cloud_api.UploadStrategy.SIMPLE:
      uploader = upload.SimpleUpload(
          client=client,
          source_stream=source_stream,
          destination_resource=destination_resource,
          request_config=request_config,
          source_resource=source_resource,
      )
    elif upload_strategy == cloud_api.UploadStrategy.RESUMABLE:
      uploader = upload.ResumableUpload(
          client=client,
          source_stream=source_stream,
          destination_resource=destination_resource,
          request_config=request_config,
          serialization_data=serialization_data,
          source_resource=source_resource,
          tracker_callback=tracker_callback,
      )
    else:  # Streaming.
      uploader = upload.StreamingUpload(
          client=client,
          source_stream=source_stream,
          destination_resource=destination_resource,
          request_config=request_config,
          source_resource=source_resource,
      )

    response = uploader.run()
    return metadata_util.get_object_resource_from_grpc_object(
        response.resource)
