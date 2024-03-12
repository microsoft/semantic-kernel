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
"""Common utilities for deleting resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.metastore import operations_util as operations_api_util
from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
import six


class ServiceDeletionWaiter(object):
  """Class for waiting for synchronous deletion of one or more Services."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    self.pending_deletes = []
    self.release_track = release_track

  def AddPendingDelete(self, service_name, operation):
    """Adds a service whose deletion to track.

    Args:
      service_name: str, the relative resource name of the service being deleted
      operation: Operation, the longrunning operation object returned by the API
        when the deletion was initiated
    """
    self.pending_deletes.append(_PendingServiceDelete(service_name, operation))

  def Wait(self):
    """Polls pending deletions and returns when they are complete."""
    encountered_errors = False
    for pending_delete in self.pending_deletes:
      try:
        operations_api_util.WaitForOperation(
            pending_delete.operation,
            'Waiting for [{}] to be deleted'.format(
                pending_delete.service_name),
            release_track=self.release_track)
      except api_util.OperationError as e:
        encountered_errors = True
        log.DeletedResource(
            pending_delete.service_name,
            kind='service',
            is_async=False,
            failed=six.text_type(e))
    return encountered_errors


class _PendingServiceDelete(object):
  """Data class holding information about a pending service deletion."""

  def __init__(self, service_name, operation):
    self.service_name = service_name
    self.operation = operation


class FederationDeletionWaiter(object):
  """Class for waiting for synchronous deletion of one or more Federations."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    self.pending_deletes = []
    self.release_track = release_track

  def AddPendingDelete(self, federation_name, operation):
    """Adds a federation whose deletion to track.

    Args:
      federation_name: str, the relative resource name of the federation being
        deleted
      operation: Operation, the longrunning operation object returned by the API
        when the deletion was initiated
    """
    self.pending_deletes.append(
        _PendingFederationDelete(federation_name, operation))

  def Wait(self):
    """Polls pending deletions and returns when they are complete."""
    encountered_errors = False
    for pending_delete in self.pending_deletes:
      try:
        operations_api_util.WaitForOperation(
            pending_delete.operation,
            'Waiting for [{}] to be deleted'.format(
                pending_delete.federation_name),
            release_track=self.release_track)
      except api_util.OperationError as e:
        encountered_errors = True
        log.DeletedResource(
            pending_delete.federation_name,
            kind='federation',
            is_async=False,
            failed=six.text_type(e))
    return encountered_errors


class _PendingFederationDelete(object):
  """Data class holding information about a pending federation deletion."""

  def __init__(self, federation_name, operation):
    self.federation_name = federation_name
    self.operation = operation
