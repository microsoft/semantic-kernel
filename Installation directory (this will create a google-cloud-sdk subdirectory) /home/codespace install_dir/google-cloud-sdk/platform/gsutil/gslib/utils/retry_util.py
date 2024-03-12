# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shared utility structures and methods for handling request retries."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import time

from apitools.base.py import http_wrapper
from gslib import thread_message
from gslib.utils import constants
from retry_decorator import retry_decorator

Retry = retry_decorator.retry  # pylint: disable=invalid-name


def LogAndHandleRetries(is_data_transfer=False, status_queue=None):
  """Higher-order function allowing retry handler to access global status queue.

  Args:
    is_data_transfer: If True, disable retries in apitools.
    status_queue: The global status queue.

  Returns:
    A retry function for retryable errors in apitools.
  """

  def WarnAfterManyRetriesHandler(retry_args):
    """Exception handler for http failures in apitools.

    If the user has had to wait several seconds since their first request, print
    a progress message to the terminal to let them know we're still retrying,
    then perform the default retry logic and post a
    gslib.thread_message.RetryableErrorMessage to the global status queue.

    Args:
      retry_args: An apitools ExceptionRetryArgs tuple.
    """
    if (retry_args.total_wait_sec is not None and
        retry_args.total_wait_sec >= constants.LONG_RETRY_WARN_SEC):
      logging.info('Retrying request, attempt #%d...', retry_args.num_retries)
    if status_queue:
      status_queue.put(
          thread_message.RetryableErrorMessage(
              retry_args.exc,
              time.time(),
              num_retries=retry_args.num_retries,
              total_wait_sec=retry_args.total_wait_sec))
    http_wrapper.HandleExceptionsAndRebuildHttpConnections(retry_args)

  def RetriesInDataTransferHandler(retry_args):
    """Exception handler that disables retries in apitools data transfers.

    Post a gslib.thread_message.RetryableErrorMessage to the global status
    queue. We handle the actual retries within the download and upload
    functions.

    Args:
      retry_args: An apitools ExceptionRetryArgs tuple.
    """
    if status_queue:
      status_queue.put(
          thread_message.RetryableErrorMessage(
              retry_args.exc,
              time.time(),
              num_retries=retry_args.num_retries,
              total_wait_sec=retry_args.total_wait_sec))
    http_wrapper.RethrowExceptionHandler(retry_args)

  if is_data_transfer:
    return RetriesInDataTransferHandler
  return WarnAfterManyRetriesHandler
