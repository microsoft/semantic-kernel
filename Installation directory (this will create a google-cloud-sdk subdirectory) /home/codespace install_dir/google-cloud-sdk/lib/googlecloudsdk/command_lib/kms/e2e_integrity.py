# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Helpers for End to End integirty verification."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions

_ERROR_MESSAGE_SUFFIX = (
    "Please try again. This should happen rarely. If the error persists, "
    "contact cloudkms-feedback@google.com. To learn more about how Cloud KMS "
    "verifies in-transit integrity, visit "
    "https://cloud.google.com/kms/docs/data-integrity-guidelines.")


class ServerSideIntegrityVerificationError(core_exceptions.Error):
  """Error raised when server reported integrity verification error."""


class ClientSideIntegrityVerificationError(core_exceptions.Error):
  """Error raised when client identifies integrity verification error."""


class ResourceNameVerificationError(core_exceptions.Error):
  """Error raised when server returned resource name differs from client provided resource name."""


def GetRequestToServerCorruptedErrorMessage():
  """Error message for when the request to server failed an integrity check."""

  return ("The request sent to the server was corrupted in-transit. {}".format(
      _ERROR_MESSAGE_SUFFIX))


def GetResponseFromServerCorruptedErrorMessage():
  """Error message for when the response from server failed an integrity check."""

  return ("The response received from the server was corrupted in-transit. {}"
          .format(_ERROR_MESSAGE_SUFFIX))


def GetResourceNameMismatchErrorMessage(request_resource_name,
                                        response_resource_name):
  return (
      "Found a mismatch between user-requested crypto resource ({})".format(
          request_resource_name) +
      "and server-reported resource used for the cryptographic operation ({}).\n"
      .format(response_resource_name) + _ERROR_MESSAGE_SUFFIX)


# LINT.IfChange(invalid_checksum_err)
def ProcessHttpBadRequestError(error):
  """Intercept INVALID_ARGUMENT errors related to checksum verification.

  Intercept INVALID_ARGUMENT errors related to checksum verification, to present
  a user-friendly message.
  All other errors are surfaced as-is.
  Args:
    error: apitools_exceptions.ProcessHttpBadRequestError.

  Raises:
    ServerSideIntegrityVerificationError: if |error| is a result of a failed
    server-side request integrity verification.
    Else, re-raises |error| as exceptions.HttpException.
  """
  exc = exceptions.HttpException(error)
  regex = re.compile(
      "The checksum in field .* did not match the data in field .*.")
  if regex.search(exc.payload.status_message) is not None:
    raise ServerSideIntegrityVerificationError(
        GetRequestToServerCorruptedErrorMessage())
  else:
    raise exc
# Code paths are prohibited from being included in this file.
# LINT.ThenChange()
