# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Utilities for calling the Composer Operations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as command_util


# TODO(b/111385813): Refactor utils into a class
def GetService(release_track=base.ReleaseTrack.GA):
  return api_util.GetClientInstance(
      release_track=release_track).projects_locations_operations


def Delete(operation_resource, release_track=base.ReleaseTrack.GA):
  """Calls the Composer Operations.Delete method.

  Args:
    operation_resource: Resource, the Composer operation resource to
        delete.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.

  Returns:
    Empty
  """
  return GetService(release_track=release_track).Delete(
      api_util.GetMessagesModule(release_track=release_track)
      .ComposerProjectsLocationsOperationsDeleteRequest(
          name=operation_resource.RelativeName()))


def Get(operation_resource, release_track=base.ReleaseTrack.GA):
  """Calls the Composer Operations.Get method.

  Args:
    operation_resource: Resource, the Composer operation resource to
        retrieve.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.

  Returns:
    Operation: the requested operation
  """
  return GetService(release_track=release_track).Get(
      api_util.GetMessagesModule(release_track=release_track)
      .ComposerProjectsLocationsOperationsGetRequest(
          name=operation_resource.RelativeName()))


def List(location_refs,
         page_size,
         limit=sys.maxsize,
         release_track=base.ReleaseTrack.GA):
  """Lists Composer Operations across all locations.

  Uses a hardcoded list of locations, as there is way to dynamically
  discover the list of supported locations. Support for new locations
  will be aligned with Cloud SDK releases.

  Args:
    location_refs: [core.resources.Resource], a list of resource reference to
        locations in which to list operations.
    page_size: An integer specifying the maximum number of resources to be
      returned in a single list call.
    limit: An integer specifying the maximum number of operations to list.
        None if all available operations should be returned.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.

  Returns:
    list: a generator over Operations within the locations in `location_refs`.
  """
  return api_util.AggregateListResults(
      api_util.GetMessagesModule(release_track=release_track)
      .ComposerProjectsLocationsOperationsListRequest,
      GetService(release_track=release_track),
      location_refs,
      'operations',
      page_size,
      limit=limit,
      location_attribute='name')


def WaitForOperation(operation, message, release_track=base.ReleaseTrack.GA):
  """Waits for an operation to complete.

  Polls the operation at least every 15 seconds, showing a progress indicator.
  Returns when the operation has completed.

  Args:
    operation: Operation Message, the operation to poll
    message: str, a message to display with the progress indicator. For
        example, 'Waiting for deletion of [some resource]'.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
        which Composer client library will be used.
  """
  waiter.WaitFor(
      _OperationPoller(release_track=release_track),
      operation.name,
      message,
      max_wait_ms=3600 * 1000,
      wait_ceiling_ms=15 * 1000)


class _OperationPoller(waiter.CloudOperationPollerNoResources):
  """ Class for polling Composer longrunning Operations. """

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(_OperationPoller, self).__init__(
        GetService(release_track=release_track), lambda x: x)

  def IsDone(self, operation):
    if operation.done:
      if operation.error:
        raise command_util.OperationError(operation.name,
                                          operation.error.message)
      return True
    return False
