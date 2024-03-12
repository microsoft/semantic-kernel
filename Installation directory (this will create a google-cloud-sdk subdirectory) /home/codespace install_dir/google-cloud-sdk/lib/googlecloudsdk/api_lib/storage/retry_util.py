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
"""Utilities for retrying requests on failures."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno

from apitools.base.py import http_wrapper as apitools_http_wrapper
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry


def set_retry_func(apitools_transfer_object):
  """Sets the retry function for the apitools transfer object.

  Replaces the Apitools' default retry function
  HandleExceptionsAndRebuildHttpConnections with a custom one which calls
  HandleExceptionsAndRebuildHttpConnections and then raise a custom exception.
  This is useful when we don't want MakeRequest method in Apitools to retry
  the http request directly and instead let the caller decide the next action.

  Args:
    apitools_transfer_object (apitools.base.py.transfer.Transfer): The
    Apitools' transfer object.
  """
  def _handle_error_and_raise(retry_args):
    # HandleExceptionsAndRebuildHttpConnections will re-raise any exception
    # that cannot be handled. For example, 404, 500, etc.
    apitools_http_wrapper.HandleExceptionsAndRebuildHttpConnections(retry_args)

    # Apitools attempts to retry all OS/socket errors, but some of them are not
    # actually retriable. These are reraised below.
    if (
        isinstance(retry_args.exc, OSError)
        and retry_args.exc.errno == errno.ENOSPC
    ):
      raise retry_args.exc

    # If apitools did not raise any error, we want to raise a custom error to
    # inform the caller to retry the request.
    raise errors.RetryableApiError()
  apitools_transfer_object.retry_func = _handle_error_and_raise


def retryer(target, should_retry_if, target_args=None, target_kwargs=None):
  """Retries the target with specific default value.

  This function is intended to be used for all gcloud storage's API requests
  that require custom retry handling (e.g downloads and uploads).

  Args:
    target (Callable): The function to call and retry.
    should_retry_if (Callable): func(exc_type, exc_value, exc_traceback, state)
        that returns True or False.
    target_args (Sequence|None): A sequence of positional arguments to be passed
        to the target.
    target_kwargs (Dict|None): A dict of keyword arguments to be passed
        to target.

  Returns:
    Whatever the target returns.
  """
  # Convert seconds to miliseconds by multiplying by 1000.
  return retry.Retryer(
      max_retrials=properties.VALUES.storage.max_retries.GetInt(),
      wait_ceiling_ms=properties.VALUES.storage.max_retry_delay.GetInt() * 1000,
      exponential_sleep_multiplier=(
          properties.VALUES.storage.exponential_sleep_multiplier.GetInt()
      )).RetryOnException(
          target,
          args=target_args,
          kwargs=target_kwargs,
          sleep_ms=properties.VALUES.storage.base_retry_delay.GetInt() * 1000,
          should_retry_if=should_retry_if)
