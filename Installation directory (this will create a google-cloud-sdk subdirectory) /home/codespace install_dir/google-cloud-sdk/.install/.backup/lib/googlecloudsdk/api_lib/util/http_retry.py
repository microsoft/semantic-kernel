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

"""Retry logic for HTTP exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions

from googlecloudsdk.core.util import retry


def RetryOnHttpStatus(status):
  """Decorator factory to automatically retry a function for HTTP errors."""

  def RetryOnHttpStatusAttribute(func):
    """Decorator to automatically retry a function for HTTP errors."""
    # pylint:disable=invalid-name
    def retryIf(exc_type, exc_value, unused_traceback, unused_state):
      return (exc_type == exceptions.HttpError and
              exc_value.status_code == status)

    # pylint:disable=invalid-name
    def wrapper(*args, **kwargs):
      retryer = retry.Retryer(max_retrials=3, exponential_sleep_multiplier=2,
                              jitter_ms=100)
      return retryer.RetryOnException(func, args, kwargs,
                                      should_retry_if=retryIf, sleep_ms=1000)
    return wrapper
  return RetryOnHttpStatusAttribute
