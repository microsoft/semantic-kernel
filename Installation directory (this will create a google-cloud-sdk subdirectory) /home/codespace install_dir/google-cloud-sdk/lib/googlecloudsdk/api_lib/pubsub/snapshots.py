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

"""Utilities for Cloud Pub/Sub Snapshots API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('pubsub', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


class _SnapshotUpdateSetting(object):
  """Data container class for updating a snapshot."""

  def __init__(self, field_name, value):
    self.field_name = field_name
    self.value = value


class SnapshotsClient(object):
  """Client for snapshots service in the Cloud Pub/Sub API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_snapshots

  def Create(self, snapshot_ref, subscription_ref, labels=None):
    """Creates a Snapshot."""
    create_req = self.messages.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.messages.CreateSnapshotRequest(
            subscription=subscription_ref.RelativeName(),
            labels=labels),
        name=snapshot_ref.RelativeName())
    return self._service.Create(create_req)

  def Get(self, snapshot_ref):
    """Gets a Snapshot.

    Args:
      snapshot_ref (Resource): Resource reference to the Snapshot to get.
    Returns:
      Snapshot: The snapshot.
    """
    get_req = self.messages.PubsubProjectsSnapshotsGetRequest(
        snapshot=snapshot_ref.RelativeName())
    return self._service.Get(get_req)

  def Delete(self, snapshot_ref):
    """Deletes a Snapshot."""
    delete_req = self.messages.PubsubProjectsSnapshotsDeleteRequest(
        snapshot=snapshot_ref.RelativeName())
    return self._service.Delete(delete_req)

  def List(self, project_ref, page_size=100):
    """Lists Snapshots for a given project.

    Args:
      project_ref (Resource): Resource reference to Project to list
        Snapshots from.
      page_size (int): the number of entries in each batch (affects requests
        made, but not the yielded results).
    Returns:
      A generator of Snapshots in the Project.
    """
    list_req = self.messages.PubsubProjectsSnapshotsListRequest(
        project=project_ref.RelativeName(),
        pageSize=page_size
    )
    return list_pager.YieldFromList(
        self._service, list_req, batch_size=page_size,
        field='snapshots', batch_size_attribute='pageSize')

  def Patch(self, snapshot_ref, labels=None):
    """Updates a Snapshot.

    Args:
      snapshot_ref (Resource): Resource reference for the snapshot to be
        updated.
      labels (LabelsValue): The Cloud labels for the snapshot.
    Returns:
      Snapshot: The updated snapshot.
    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
    """
    update_settings = [_SnapshotUpdateSetting('labels', labels)]
    snapshot = self.messages.Snapshot(
        name=snapshot_ref.RelativeName())
    update_mask = []
    for update_setting in update_settings:
      if update_setting.value is not None:
        setattr(snapshot, update_setting.field_name, update_setting.value)
        update_mask.append(update_setting.field_name)
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    patch_req = self.messages.PubsubProjectsSnapshotsPatchRequest(
        updateSnapshotRequest=self.messages.UpdateSnapshotRequest(
            snapshot=snapshot,
            updateMask=','.join(update_mask)),
        name=snapshot_ref.RelativeName())

    return self._service.Patch(patch_req)
