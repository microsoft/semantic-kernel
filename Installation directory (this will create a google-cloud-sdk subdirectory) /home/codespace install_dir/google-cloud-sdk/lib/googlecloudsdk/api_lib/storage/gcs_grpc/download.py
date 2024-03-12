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
"""Download workflow used by GCS gRPC client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import gcs_download
from googlecloudsdk.api_lib.storage.gcs_grpc import grpc_util
from googlecloudsdk.api_lib.storage.gcs_grpc import retry_util


class GrpcDownload(gcs_download.GcsDownload):
  """Perform GCS Download using gRPC API."""

  def __init__(self,
               gapic_client,
               cloud_resource,
               download_stream,
               start_byte,
               end_byte,
               digesters,
               progress_callback,
               download_strategy,
               decryption_key):
    """Initializes a GrpcDownload instance.

    Args:
      gapic_client (StorageClient): The GAPIC API client to interact with
        GCS using gRPC.
      cloud_resource (resource_reference.ObjectResource): See
        cloud_api.CloudApi.download_object.
      download_stream (stream): Stream to send the object data to.
      start_byte (int): See super class.
      end_byte (int): See super class.
      digesters (dict): See cloud_api.CloudApi.download_object.
      progress_callback (function): See cloud_api.CloudApi.download_object.
      download_strategy (cloud_api.DownloadStrategy): Download strategy used to
        perform the download.
      decryption_key (encryption_util.EncryptionKey|None): The decryption key
        to be used to download the object if the object is encrypted.
    """
    super(__class__, self).__init__(download_stream, start_byte, end_byte)
    self._gapic_client = gapic_client
    self._cloud_resource = cloud_resource
    self._digesters = digesters
    self._progress_callback = progress_callback
    self._download_strategy = download_strategy
    self._decryption_key = decryption_key

  def should_retry(self, exc_type, exc_value, exc_traceback):
    """See super class."""
    return retry_util.is_retriable(exc_type, exc_value, exc_traceback)

  def launch(self):
    """See super class."""
    return grpc_util.download_object(
        gapic_client=self._gapic_client,
        cloud_resource=self._cloud_resource,
        download_stream=self._download_stream,
        digesters=self._digesters,
        progress_callback=self._progress_callback,
        start_byte=self._start_byte,
        end_byte=self._end_byte,
        download_strategy=self._download_strategy,
        decryption_key=self._decryption_key,
    )

  @retry_util.grpc_default_retryer
  def simple_download(self):
    """Downloads the object.

    On retriable errors, the entire download will be re-performed instead of
    resuming from a particular byte. This is useful for streaming download
    cases.

    Unlike Apitools, the GAPIC client doesn't retry the request by
    default, hence we are using the decorator.

    Returns:
      Encoding string for object if requested. Otherwise, None.
    """
    return self.launch()

  def run(self):
    """See super class."""
    if self._download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
      return self.simple_download()
    else:
      return super(__class__, self).run(retriable_in_flight=True)
