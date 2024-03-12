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
"""Utilities for GCS errors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.storage import errors as cloud_errors

ERROR_TRANSLATION = [
    (
        apitools_exceptions.HttpNotFoundError,
        None,
        cloud_errors.GcsNotFoundError,
    ),
    (
        apitools_exceptions.HttpError,
        409,
        cloud_errors.GcsConflictError,
    ),
    (
        apitools_exceptions.HttpError,
        412,
        cloud_errors.GcsPreconditionFailedError,
    ),
    (apitools_exceptions.HttpError, None, cloud_errors.GcsApiError),
]


def get_status_code(error):
  if error.response:
    return error.response.get('status')


def catch_http_error_raise_gcs_api_error(format_str=None):
  """Decorator catches HttpError and returns GcsApiError with custom message.

  Args:
    format_str (str): A googlecloudsdk.api_lib.util.exceptions.HttpErrorPayload
      format string. Note that any properties that are accessed here are on the
      HttpErrorPayload object, not the object returned from the server.

  Returns:
    A decorator that catches apitools.HttpError and returns GcsApiError with a
      customizable error message.
  """
  return cloud_errors.catch_error_raise_cloud_api_error(
      ERROR_TRANSLATION,
      format_str=format_str,
      status_code_getter=get_status_code,
  )
