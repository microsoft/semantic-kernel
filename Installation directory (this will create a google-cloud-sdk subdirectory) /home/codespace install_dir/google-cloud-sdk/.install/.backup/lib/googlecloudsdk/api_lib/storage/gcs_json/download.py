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
"""Implementation functions for downloads from the Google Cloud Storage API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import http_wrapper as apitools_http_wrapper

from googlecloudsdk.api_lib.storage import errors as cloud_errors
from googlecloudsdk.api_lib.storage import retry_util
from googlecloudsdk.calliope import exceptions as calliope_errors
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

import oauth2client


def _no_op_callback(unused_response, unused_object):
  """Disables Apitools' default print callbacks."""
  pass


def launch(apitools_download,
           start_byte=0,
           end_byte=None,
           additional_headers=None):
  """GCS-specific download implementation.

  Args:
    apitools_download (apitools.transfer.Download): Apitools object for managing
      downloads.
    start_byte (int): Starting point for download (for resumable downloads and
      range requests). Can be set to negative to request a range of bytes
      (python equivalent of [:-3]).
    end_byte (int): Ending byte number, inclusive, for download (for range
      requests). If None, download the rest of the object.
    additional_headers (dict|None): Headers to add to HTTP request.

  Returns:
    Encoding string for object if requested. Otherwise, None.
  """
  if start_byte or end_byte is not None:
    apitools_download.GetRange(
        additional_headers=additional_headers,
        start=start_byte,
        end=end_byte,
        use_chunks=False)
  else:
    apitools_download.StreamMedia(
        additional_headers=additional_headers,
        callback=_no_op_callback,
        finish_callback=_no_op_callback,
        use_chunks=False)
  return apitools_download.encoding


def launch_retriable(download_stream,
                     apitools_download,
                     start_byte=0,
                     end_byte=None,
                     additional_headers=None):
  """Wraps download to make it retriable."""
  # Hack because nonlocal keyword causes Python 2 syntax error.
  progress_state = {'start_byte': start_byte}
  retry_util.set_retry_func(apitools_download)

  def _should_retry_resumable_download(exc_type, exc_value, exc_traceback,
                                       state):
    converted_error, _ = calliope_errors.ConvertKnownError(exc_value)
    if isinstance(exc_value, oauth2client.client.HttpAccessTokenRefreshError):
      if exc_value.status < 500 and exc_value.status != 429:
        # Not server error or too many requests error.
        return False
    elif not (isinstance(converted_error, core_exceptions.NetworkIssueError) or
              isinstance(converted_error, cloud_errors.RetryableApiError)):
      # Not known transient network error.
      return False

    start_byte = download_stream.tell()
    if start_byte > progress_state['start_byte']:
      # We've made progress, so allow a fresh set of retries.
      progress_state['start_byte'] = start_byte
      state.retrial = 0
    log.debug('Retrying download from byte {} after exception: {}.'
              ' Trace: {}'.format(start_byte, exc_type, exc_traceback))

    apitools_http_wrapper.RebuildHttpConnections(apitools_download.bytes_http)
    return True

  def _call_launch():
    return launch(
        apitools_download,
        start_byte=progress_state['start_byte'],
        end_byte=end_byte,
        additional_headers=additional_headers)

  return retry_util.retryer(
      target=_call_launch, should_retry_if=_should_retry_resumable_download)
