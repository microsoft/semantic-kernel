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
"""Utilities for retrying requests on failures for gRPC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import sys

from google.auth import exceptions as auth_exceptions
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import retry_util

import requests

# pylint:disable=g-import-not-at-top
# TODO(b/277356731) Remove version check after gcloud drops Python <= 3.5.
if sys.version_info.major == 3 and sys.version_info.minor > 5:
  from google.api_core import exceptions
# pylint:enable=g-import-not-at-top


def is_retriable(exc_type=None, exc_value=None, exc_traceback=None, state=None):
  """Returns True if the error is retriable."""
  # These are not used, but the signature for retry_util.retryer's
  # should_retry_if parameter requires these parameters to be present.
  del exc_type, exc_traceback, state

  return isinstance(exc_value, (
      auth_exceptions.TransportError,
      errors.RetryableApiError,
      exceptions.BadGateway,
      exceptions.GatewayTimeout,
      exceptions.InternalServerError,
      exceptions.TooManyRequests,
      exceptions.ServiceUnavailable,
      requests.exceptions.ConnectionError,
      requests.exceptions.ChunkedEncodingError,
      requests.exceptions.Timeout,
      ConnectionError))


def grpc_default_retryer(func):
  """A decorator to retry on transient errors."""
  @functools.wraps(func)
  def wrapped_func(*args, **kwargs):
    return retry_util.retryer(
        target=func,
        should_retry_if=is_retriable,
        target_args=args,
        target_kwargs=kwargs)

  return wrapped_func

