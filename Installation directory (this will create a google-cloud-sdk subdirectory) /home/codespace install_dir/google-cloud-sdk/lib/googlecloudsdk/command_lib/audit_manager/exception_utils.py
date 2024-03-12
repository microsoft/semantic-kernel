# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Helpers for exceptions raised by Audit Manager."""

from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.core import exceptions as gcloud_core_exceptions


ERROR_FORMAT = 'Error: {status_code}. {status_message}'
ERROR_REASON_NO_ORGANISATION_FOUND = (
    'ERROR_CODE_NO_ORGANISATION_FOUND_FOR_RESOURCE'
)
ERROR_REASON_NOT_ENROLLED = 'ERROR_CODE_RESOURCE_NOT_ENROLLED'
ERROR_REASON_PERMISSION_DENIED = 'IAM_PERMISSION_DENIED'


def ExtractReasons(e):
  details = e.payload.type_details['ErrorInfo']

  if details is None:
    return None

  return [d['reason'] for d in details]


class AuditManagerError(gcloud_core_exceptions.Error):
  """Custom error class for Audit Manager related exceptions.

  Attributes:
    http_exception: core http exception thrown by gcloud
    suggested_command_purpose: what the suggested command achieves
    suggested_command: suggested command to help fix the exception
  """

  def __init__(
      self,
      error,
      suggested_command_purpose=None,
      suggested_command=None,
  ):
    self.http_exception = gcloud_exception.HttpException(error, ERROR_FORMAT)
    self.suggested_command_purpose = suggested_command_purpose
    self.suggested_command = suggested_command

  def __str__(self):
    message = f'{self.http_exception}'

    if self.suggested_command_purpose is not None:
      message += (
          '\n\nRun the following command to'
          f' {self.suggested_command_purpose}:\n\n{self.suggested_command}'
      )

    return message

  @property
  def error_info(self):
    return self.http_exception.payload.type_details['ErrorInfo']

  def has_error_info(self, reason):
    return reason in [e['reason'] for e in self.error_info]
