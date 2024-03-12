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
"""Common download workflow used by GCS API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import retry_util
from googlecloudsdk.core import log


class GcsDownload(object):
  """Base class for performing GCS downloads."""

  def __init__(self, download_stream, start_byte, end_byte):
    """Initializes a GcsDownload instance.

    Args:
      download_stream (stream): Stream to send the object data to.
      start_byte (int): Starting point for download (for resumable downloads and
        range requests). Can be set to negative to request a range of bytes
        (python equivalent of [:-3]).
      end_byte (int): Ending byte number, inclusive, for download (for range
        requests). If None, download the rest of the object.

    """
    self._download_stream = download_stream
    self._initial_start_byte = start_byte
    self._end_byte = end_byte
    self._start_byte = start_byte

  def should_retry(self, exc_type, exc_value, exc_traceback):
    """Returns True if the error should be retried."""
    raise NotImplementedError()

  def launch(self):
    """Performs the download.

    The child classes should implement this function.

    Returns:
      Encoding string for object if requested. Otherwise, None.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError()

  def _should_retry_wrapper(self, exc_type, exc_value, exc_traceback, state):
    """Returns True if the error should be retried.

    This method also updates the start_byte to be used for request
    to be retried.

    Args:
      exc_type (type): The type of Exception.
      exc_value (Exception): The error instance.
      exc_traceback (traceback): The traceback for the exception.
      state (core.util.retry.RetryState): The state object
        maintained by the retryer.

    Returns:
      True if the error should be retried.
    """
    if not self.should_retry(exc_type, exc_value, exc_traceback):
      return False

    # Set the correct start byte
    start_byte = self._download_stream.tell()
    if start_byte > self._start_byte:
      # We've made progress, so allow a fresh set of retries.
      self._start_byte = start_byte
      state.retrial = 0
    log.debug('Retrying download from byte {} after exception: {}.'
              ' Trace: {}'.format(start_byte, exc_type, exc_traceback))
    return True

  def run(self, retriable_in_flight=True):
    """Performs downlaod.

    Args:
      retriable_in_flight (bool): Indicates if a download can be retried
        on network error, resuming the download from the last downloaded byte.

    Returns:
      The result returned by launch method.
    """
    if not retriable_in_flight:
      return self.launch()

    return retry_util.retryer(
        target=self.launch, should_retry_if=self._should_retry_wrapper)
