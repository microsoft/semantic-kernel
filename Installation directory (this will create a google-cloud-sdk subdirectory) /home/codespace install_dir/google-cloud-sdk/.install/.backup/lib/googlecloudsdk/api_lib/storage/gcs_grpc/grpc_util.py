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
"""Helper functions for making gRPC API calls."""

# TODO(b/271932922): Move functions from here to its own client class.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as cloud_errors
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.core import log


def get_full_bucket_name(bucket_name):
  """Returns the bucket resource name as expected by gRPC API."""
  return 'projects/_/buckets/{}'.format(bucket_name)


def _get_encryption_request_params(gapic_client, decryption_key):
  if (decryption_key is not None
      and decryption_key.type == encryption_util.KeyType.CSEK):
    return gapic_client.types.CommonObjectRequestParams(
        encryption_algorithm=encryption_util.ENCRYPTION_ALGORITHM,
        encryption_key_bytes=base64.b64decode(
            decryption_key.key.encode('utf-8')),
        encryption_key_sha256_bytes=base64.b64decode(
            decryption_key.sha256.encode('utf-8')),
    )
  else:
    return None


def download_object(gapic_client,
                    cloud_resource,
                    download_stream,
                    digesters,
                    progress_callback,
                    start_byte,
                    end_byte,
                    download_strategy,
                    decryption_key):
  """Downloads the object using gRPC."""
  # Initialize request arguments.
  bucket_name = get_full_bucket_name(cloud_resource.storage_url.bucket_name)

  request = gapic_client.types.ReadObjectRequest(
      bucket=bucket_name,
      object_=cloud_resource.storage_url.object_name,
      generation=(
          int(cloud_resource.generation) if cloud_resource.generation else None
      ),
      read_offset=start_byte,
      read_limit=end_byte - start_byte + 1 if end_byte is not None else 0,
      common_object_request_params=_get_encryption_request_params(
          gapic_client, decryption_key
      ),
  )

  # Make the request.
  stream = gapic_client.storage.read_object(request=request)

  # Handle the response.
  processed_bytes = start_byte
  # For example, can happen if piping to a command that only reads one line.
  destination_pipe_is_broken = False
  for response in stream:
    data = response.checksummed_data.content
    if data:
      try:
        download_stream.write(data)
      except BrokenPipeError:
        if download_strategy is cloud_api.DownloadStrategy.ONE_SHOT:
          log.info('Writing to download stream raised broken pipe error.')
          destination_pipe_is_broken = True
          break
        raise

      if digesters:
        for hash_object in digesters.values():
          hash_object.update(data)

      processed_bytes += len(data)
      if progress_callback:
        progress_callback(processed_bytes)

  target_size = (
      end_byte - start_byte + 1 if end_byte is not None else cloud_resource.size
  )
  total_downloaded_data = processed_bytes - start_byte
  if target_size != total_downloaded_data and not destination_pipe_is_broken:
    # The input stream terminated before the entire content was read,
    # possibly due to a network condition.
    message = (
        'Download not completed. Target size={}, downloaded data={}.'
        ' The input stream terminated before the entire content was read,'
        ' possibly due to a network condition.'.format(
            target_size, total_downloaded_data))
    log.debug(message)
    raise cloud_errors.RetryableApiError(message)
