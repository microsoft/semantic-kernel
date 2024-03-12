# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Commands for interacting with the Cloud NetApp Files Volume Snapshot API resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.netapp import constants
from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class SnapshotsClient(object):
  """Wrapper for working with Snapshots in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    if release_track == base.ReleaseTrack.ALPHA:
      self._adapter = AlphaSnapshotsAdapter()
    elif release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaSnapshotsAdapter()
    elif release_track == base.ReleaseTrack.GA:
      self._adapter = SnapshotsAdapter()
    else:
      raise ValueError('[{}] is not a valid API version.'.format(
          netapp_api_util.VERSION_MAP[release_track]))

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Waits on the long-running operation until the done field is True.

    Args:
      operation_ref: the operation reference.

    Raises:
      waiter.OperationError: if the operation contains an error.

    Returns:
      the 'response' field of the Operation.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations
        ),
        operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()),
    )

  def CreateSnapshot(self, snapshot_ref, volume_ref, async_, config):
    """Create a Cloud NetApp Volume Snapshot."""
    request = (
        self.messages.NetappProjectsLocationsVolumesSnapshotsCreateRequest(
            parent=volume_ref, snapshotId=snapshot_ref.Name(), snapshot=config
        )
    )
    create_op = self.client.projects_locations_volumes_snapshots.Create(request)
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseSnapshotConfig(self, name=None, description=None, labels=None):
    """Parses the command line arguments for Create Snapshot into a config.

    Args:
      name: the name of the Snapshot.
      description: the description of the Snapshot.
      labels: the parsed labels value.

    Returns:
      the configuration that will be used as the request body for creating a
      Cloud NetApp Files Snapshot.
    """
    snapshot = self.messages.Snapshot()
    snapshot.name = name
    snapshot.description = description
    snapshot.labels = labels
    return snapshot

  def ListSnapshots(self, volume_ref, limit=None):
    """Make API calls to List active Cloud NetApp Volume Snapshots.

    Args:
      volume_ref: The parent Volume to list NetApp Volume Snapshots.
      limit: The number of Cloud NetApp Volume Snapshots to limit the results
        to. This limit is passed to the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp Volume Snapshots.
    """
    request = self.messages.NetappProjectsLocationsVolumesSnapshotsListRequest(
        parent=volume_ref)
    log.status.Print('request: {}'.format(request))
    # Check for unreachable locations.
    response = self.client.projects_locations_volumes_snapshots.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_volumes_snapshots,
        request,
        field=constants.SNAPSHOT_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def DeleteSnapshot(self, snapshot_ref, async_):
    """Deletes an existing Cloud NetApp Volume Snapshot."""
    request = (
        self.messages.NetappProjectsLocationsVolumesSnapshotsDeleteRequest(
            name=snapshot_ref.RelativeName()
        )
    )
    return self._DeleteSnapshot(async_, request)

  def _DeleteSnapshot(self, async_, request):
    delete_op = self.client.projects_locations_volumes_snapshots.Delete(request)
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)

  def GetSnapshot(self, snapshot_ref):
    """Get Cloud NetApp Snapshot information."""
    request = self.messages.NetappProjectsLocationsVolumesSnapshotsGetRequest(
        name=snapshot_ref.RelativeName())
    return self.client.projects_locations_volumes_snapshots.Get(request)

  def ParseUpdatedSnapshotConfig(self,
                                 snapshot_config,
                                 description=None,
                                 labels=None):
    """Parses updates into a snapshot config.

    Args:
      snapshot_config: The snapshot config to update.
      description: str, a new description, if any.
      labels: LabelsValue message, the new labels value, if any.

    Returns:
      The snapshot message.
    """
    return self._adapter.ParseUpdatedSnapshotConfig(
        snapshot_config,
        description=description,
        labels=labels)

  def UpdateSnapshot(self, snapshot_ref, snapshot_config, update_mask, async_):
    """Updates a Cloud NetApp Snapshot.

    Args:
      snapshot_ref: the reference to the Snapshot.
      snapshot_config: Snapshot config, the updated snapshot.
      update_mask: str, a comma-separated list of updated fields.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      an Operation or Volume message.
    """
    update_op = self._adapter.UpdateSnapshot(snapshot_ref, snapshot_config,
                                             update_mask)
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)


class SnapshotsAdapter(object):
  """Adapter for the Cloud NetApp Files API Snapshot resource."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.GA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )

  def UpdateSnapshot(self, snapshot_ref, snapshot_config, update_mask):
    """Send a Patch request for the Cloud NetApp Snapshot."""
    update_request = (
        self.messages.NetappProjectsLocationsVolumesSnapshotsPatchRequest(
            snapshot=snapshot_config,
            name=snapshot_ref.RelativeName(),
            updateMask=update_mask))
    update_op = self.client.projects_locations_volumes_snapshots.Patch(
        update_request)
    return update_op

  def ParseUpdatedSnapshotConfig(self,
                                 snapshot_config,
                                 description=None,
                                 labels=None):
    """Parse update information into an updated Snapshot message."""
    if description is not None:
      snapshot_config.description = description
    if labels is not None:
      snapshot_config.labels = labels
    return snapshot_config


class BetaSnapshotsAdapter(SnapshotsAdapter):
  """Adapter for the Beta Cloud NetApp Files API Snapshot resource."""

  def __init__(self):
    super(BetaSnapshotsAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )


class AlphaSnapshotsAdapter(BetaSnapshotsAdapter):
  """Adapter for the Alpha Cloud NetApp Files API Snapshot resource."""

  def __init__(self):
    super(AlphaSnapshotsAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.ALPHA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )
