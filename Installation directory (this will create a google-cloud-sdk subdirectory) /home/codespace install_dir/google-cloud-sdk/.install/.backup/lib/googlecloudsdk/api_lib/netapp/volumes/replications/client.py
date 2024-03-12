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
"""Commands for interacting with the Cloud NetApp Files Volume Replication API resource."""

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


class ReplicationsClient(object):
  """Wrapper for working with Replications in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    if release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaReplicationsAdapter()
    elif release_track == base.ReleaseTrack.GA:
      self._adapter = ReplicationsAdapter()
    else:
      raise ValueError(
          '[{}] is not a valid API version.'.format(
              netapp_api_util.VERSION_MAP[release_track]
          )
      )

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Wait on the long-running operation until the done field is True.

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

  def CreateReplication(self, replication_ref, volume_ref, async_, config):
    """Creates a Cloud NetApp Volume Replication."""
    request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsCreateRequest(
            parent=volume_ref,
            replicationId=replication_ref.Name(),
            replication=config,
        )
    )
    create_op = self.client.projects_locations_volumes_replications.Create(
        request
    )
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseReplicationConfig(
      self,
      name=None,
      description=None,
      labels=None,
      replication_schedule=None,
      destination_volume_parameters=None,
  ):
    """Parse the command line arguments for Create Replication into a config.

    Args:
      name: the name of the Replication.
      description: the description of the Replication.
      labels: the parsed labels value.
      replication_schedule: the schedule for Replication.
      destination_volume_parameters: the input parameters used for creating
        destination volume.

    Returns:
      the configuration that will be used as the request body for creating a
      Cloud NetApp Files Replication.
    """
    replication = self.messages.Replication()
    replication.name = name
    replication.description = description
    replication.labels = labels
    replication.replicationSchedule = replication_schedule
    self._adapter.ParseDestinationVolumeParameters(
        replication, destination_volume_parameters
    )
    return replication

  def ListReplications(self, volume_ref, limit=None):
    """List all active Cloud NetApp Volume Replications.

    Args:
      volume_ref: The parent Volume to list NetApp Volume Replications.
      limit: The number of Cloud NetApp Volume Replications to limit the results
        to. This limit is passed to the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp Volume Replications.
    """
    request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsListRequest(
            parent=volume_ref
        )
    )
    # Check for unreachable locations.
    response = self.client.projects_locations_volumes_replications.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_volumes_replications,
        request,
        field=constants.REPLICATION_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def DeleteReplication(self, replication_ref, async_):
    """Delete an existing Cloud NetApp Volume Replication."""
    request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsDeleteRequest(
            name=replication_ref.RelativeName()
        )
    )
    return self._DeleteReplication(async_, request)

  def _DeleteReplication(self, async_, request):
    delete_op = self.client.projects_locations_volumes_replications.Delete(
        request
    )
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def GetReplication(self, replication_ref):
    """Get information of a Cloud NetApp Volume Replication."""
    request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsGetRequest(
            name=replication_ref.RelativeName()
        )
    )
    return self.client.projects_locations_volumes_replications.Get(request)

  def ParseUpdatedReplicationConfig(
      self, replication_config, description=None, labels=None,
      replication_schedule=None
  ):
    """Parse updates into a replication config.

    Args:
      replication_config: The replication config to update.
      description: The new description, if any.
      labels: LabelsValue message, the new labels value, if any.
      replication_schedule: The new schedule for Replication, if any.

    Returns:
      The replication message.
    """
    return self._adapter.ParseUpdatedReplicationConfig(
        replication_config, description=description, labels=labels,
        replication_schedule=replication_schedule
    )

  def UpdateReplication(
      self, replication_ref, replication_config, update_mask, async_
  ):
    """Update a Cloud NetApp Volume Replication.

    Args:
      replication_ref: the reference to the Replication.
      replication_config: Replication config, the updated replication.
      update_mask: str, a comma-separated list of updated fields.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      an Operation or Volume message.
    """
    update_op = self._adapter.UpdateReplication(
        replication_ref, replication_config, update_mask
    )
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ResumeReplication(
      self, replication_ref, async_
  ):
    """Resume a Cloud NetApp Volume Replication.

    Args:
      replication_ref: the reference to the Replication.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      an Operation or Volume message.
    """
    resume_op = self._adapter.ResumeReplication(replication_ref)
    if async_:
      return resume_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        resume_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ReverseReplication(
      self, replication_ref, async_
  ):
    """Reverse the direction of a Cloud NetApp Volume Replication.

    Args:
      replication_ref: the reference to the Replication.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      an Operation if async_ is set to true, or a Replication message if the
      ReverseReplicationDirectionRequest is successful.
    """
    reverse_op = self._adapter.ReverseReplication(replication_ref)
    if async_:
      return reverse_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        reverse_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def StopReplication(self, replication_ref, async_, force):
    """Stop a Cloud NetApp Volume Replication.

    Args:
      replication_ref: the reference to the Replication.
      async_: bool, if False, wait for the operation to complete.
      force: bool, if True, call stop Replication with force parameter set to
        True.

    Returns:
      an Operation or Volume message.
    """
    stop_op = self._adapter.StopReplication(replication_ref, force)
    if async_:
      return stop_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        stop_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)


class ReplicationsAdapter(object):
  """Adapter for the Cloud NetApp Files API Replication resource."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.GA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )

  def ParseDestinationVolumeParameters(
      self, replication, destination_volume_parameters
  ):
    """Parses Destination Volume Parameters for Replication into a config.

    Args:
      replication: The Cloud Netapp Volumes Replication object.
      destination_volume_parameters: The Destination Volume Parameters message
        object.

    Returns:
      Replication message populated with Destination Volume Parameters values.
    """
    if not destination_volume_parameters:
      return
    parameters = self.messages.DestinationVolumeParameters()
    for key, val in destination_volume_parameters.items():
      if key == 'storage_pool':
        parameters.storagePool = val
      elif key == 'volume_id':
        parameters.volumeId = val
      elif key == 'share_name':
        parameters.shareName = val
      elif key == 'description':
        parameters.description = val
      else:
        log.warning('The attribute {} is not recognized.'.format(key))
    replication.destinationVolumeParameters = parameters

  def UpdateReplication(self, replication_ref, replication_config, update_mask):
    """Send a Patch request for the Cloud NetApp Volume Replication."""
    update_request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsPatchRequest(
            replication=replication_config,
            name=replication_ref.RelativeName(),
            updateMask=update_mask,
        )
    )
    update_op = self.client.projects_locations_volumes_replications.Patch(
        update_request
    )
    return update_op

  def ParseUpdatedReplicationConfig(
      self, replication_config, description=None, labels=None,
      replication_schedule=None
  ):
    """Parse update information into an updated Replication message."""
    if description is not None:
      replication_config.description = description
    if labels is not None:
      replication_config.labels = labels
    if replication_schedule is not None:
      replication_config.replicationSchedule = replication_schedule
    return replication_config

  def ResumeReplication(self, replication_ref):
    """Send a resume request for the Cloud NetApp Volume Replication."""
    resume_request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsResumeRequest(
            name=replication_ref.RelativeName(),
        )
    )
    return self.client.projects_locations_volumes_replications.Resume(
        resume_request
    )

  def ReverseReplication(self, replication_ref):
    """Send a reverse request for the Cloud NetApp Volume Replication."""
    reverse_request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsReverseDirectionRequest(
            name=replication_ref.RelativeName(),
        )
    )
    return self.client.projects_locations_volumes_replications.ReverseDirection(
        reverse_request
    )

  def StopReplication(self, replication_ref, force):
    """Send a stop request for the Cloud NetApp Volume Replication."""
    stop_request = (
        self.messages.NetappProjectsLocationsVolumesReplicationsStopRequest(
            name=replication_ref.RelativeName(),
            stopReplicationRequest=self.messages.StopReplicationRequest(
                force=force
            ),
        )
    )
    return self.client.projects_locations_volumes_replications.Stop(
        stop_request
    )


class BetaReplicationsAdapter(ReplicationsAdapter):
  """Adapter for the Beta Cloud NetApp Files API Replication resource."""

  def __init__(self):
    super(BetaReplicationsAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )
