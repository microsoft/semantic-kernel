# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Useful commands for interacting with the Cloud Datastore Operations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


_OPERATIONS_API_VERSION = 'v1'
DEFAULT_PAGE_SIZE = 100


def GetClient():
  """Returns the Cloud Datastore client for operations."""
  return apis.GetClientInstance('datastore', _OPERATIONS_API_VERSION)


def GetService():
  """Returns the service for interacting with the Operations service."""
  return GetClient().projects_operations


def GetMessages():
  """Import and return the appropriate operations messages module."""
  return apis.GetMessagesModule('datastore', _OPERATIONS_API_VERSION)


def ListOperations(project, limit=None, operation_filter=None):
  """Lists all of the Datastore operations.

  Args:
    project: the project to list operations for, a string.
    limit: the maximum number of operations to return, an integer. Defaults to
      positive infinity if unset.
    operation_filter: a filter to apply to operations, a string.

  Returns:
    a generator of google.longrunning.Operations.
  """
  list_request = GetMessages().DatastoreProjectsOperationsListRequest(
      filter=operation_filter, name='projects/{0}'.format(project))
  batch_size = limit if limit else DEFAULT_PAGE_SIZE
  return list_pager.YieldFromList(
      GetService(),
      list_request,
      limit=limit,
      batch_size=batch_size,
      field='operations',
      batch_size_attribute='pageSize')


def GetOperation(name):
  """Returns the google.longrunning.Operation with the given name."""
  return GetService().Get(
      GetMessages().DatastoreProjectsOperationsGetRequest(name=name))


def CancelOperation(name):
  """Cancels the google.longrunning.Operation with the given name."""
  return GetService().Cancel(
      GetMessages().DatastoreProjectsOperationsCancelRequest(name=name))


def DeleteOperation(name):
  """Deletes the google.longrunning.Operation with the given name."""
  return GetService().Delete(
      GetMessages().DatastoreProjectsOperationsDeleteRequest(name=name))


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  operation_ref = resources.REGISTRY.Parse(
      operation.name, collection='datastore.projects.operations')
  poller = waiter.CloudOperationPollerNoResources(GetService())
  return waiter.WaitFor(
      poller, operation_ref,
      'Waiting for [{0}] to finish'.format(operation_ref.RelativeName()))
