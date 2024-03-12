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
"""Utilities for calling the Metastore Operations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


def GetOperation(release_track=base.ReleaseTrack.GA):
  return api_util.GetClientInstance(
      release_track=release_track
  ).projects_locations_operations


def Cancel(relative_resource_name, release_track=base.ReleaseTrack.ALPHA):
  """Calls the Metastore Operations.Cancel method.

  Args:
    relative_resource_name: str, the relative resource name of the Metastore
      operation to cancel.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Dataproc Metastore client library will be used.

  Returns:
    Empty
  """
  return GetOperation(release_track=release_track).Cancel(
      api_util.GetMessagesModule(
          release_track=release_track
      ).MetastoreProjectsLocationsOperationsCancelRequest(
          name=relative_resource_name
      )
  )


def Delete(relative_resource_name, release_track=base.ReleaseTrack.GA):
  """Calls the Metastore Operations.Delete method.

  Args:
    relative_resource_name: str, the relative resource name of the Metastore
      operation to delete.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Dataproc Metastore client library will be used.

  Returns:
    Empty
  """
  return GetOperation(release_track=release_track).Delete(
      api_util.GetMessagesModule(
          release_track=release_track
      ).MetastoreProjectsLocationsOperationsDeleteRequest(
          name=relative_resource_name
      )
  )


def PollAndReturnOperation(
    operation, message, release_track=base.ReleaseTrack.GA
):
  """Waits for an operation to complete and return it.

  Polls the operation at least every 15 seconds, showing a progress indicator.
  Returns when the operation has completed. The timeout periods of this
  operation is one hour.

  Args:
    operation: Operation Message, the operation to poll
    message: str, a message to display with the progress indicator. For example,
      'Waiting for deletion of [some resource]'.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Metastore client library will be used.

  Returns:
    poller.GetResult(operation).
  """
  return waiter.WaitFor(
      _OperationPollerWithError(release_track=release_track),
      operation.name,
      message,
      max_wait_ms=3600 * 1000,
      wait_ceiling_ms=15 * 1000,
  )


def WaitForOperation(operation, message, release_track=base.ReleaseTrack.GA):
  """Waits for an operation to complete.

  Polls the operation at least every 15 seconds, showing a progress indicator.
  Returns when the operation has completed.

  Args:
    operation: Operation Message, the operation to poll
    message: str, a message to display with the progress indicator. For example,
      'Waiting for deletion of [some resource]'.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Metastore client library will be used.
  """
  waiter.WaitFor(
      _OperationPoller(release_track=release_track),
      operation.name,
      message,
      max_wait_ms=3600 * 1000,
      wait_ceiling_ms=15 * 1000,
  )


class _OperationPoller(waiter.CloudOperationPollerNoResources):
  """Class for polling Metastore longrunning Operations."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(_OperationPoller, self).__init__(
        GetOperation(release_track=release_track), lambda x: x
    )

  def IsDone(self, operation):
    if not operation.done:
      return False
    if operation.error:
      raise api_util.OperationError(operation.name, operation.error.message)
    return True


class _OperationPollerWithError(waiter.CloudOperationPollerNoResources):
  """Class for polling Metastore longrunning Operations and print errors."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(_OperationPollerWithError, self).__init__(
        GetOperation(release_track=release_track), lambda x: x
    )

  def IsDone(self, operation):
    if not operation.done:
      return False
    if operation.error:
      if operation.error.code:
        log.status.Print("Status Code:", operation.error.code)
      if operation.error.message:
        log.status.Print("Error message:", operation.error.message)
      if operation.error.details:
        for message in operation.error.details[0].additionalProperties:
          if message.key == "details":
            log.status.Print(
                "Error details:",
                message.value.object_value.properties[0].value.string_value,
            )
      raise api_util.OperationError(operation.name, "")
    return True
