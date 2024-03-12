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
"""Cloud Bare Metal Solution client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as apilib_exceptions
from googlecloudsdk.command_lib.bms import util


import six

_DEFAULT_API_VERSION = 'v2'
_V1_API_VERSION = 'v1'
_GLOBAL_REGION = 'global'
_REGIONAL_IAM_REGEX = re.compile(
    "PERMISSION_DENIED: Permission (.+) denied on 'projects/(.+?)/.*")

IpRangeReservation = collections.namedtuple(
    'IpRangeReservation', ['start_address', 'end_address', 'note'])


def _ParseError(error):
  """Returns a best-effort error message created from an API client error."""
  if isinstance(error, apitools_exceptions.HttpError):
    parsed_error = apilib_exceptions.HttpException(error,
                                                   error_format='{message}')
    error_message = parsed_error.message
  else:
    error_message = six.text_type(error)
  return error_message


def _CollapseRegionalIAMErrors(errors):
  """If all errors are PERMISSION_DENIEDs, use a single global error instead."""
  # TODO(b/198857865): Remove this hack once the `global` region fix is in
  if errors:
    matches = [_REGIONAL_IAM_REGEX.match(e) for e in errors]
    if (all(match is not None for match in matches)
        and len(set(match.group(1) for match in matches)) == 1):
      errors = ['PERMISSION_DENIED: Permission %s denied on projects/%s' %
                (matches[0].group(1), matches[0].group(2))]
  return errors


class BmsClient(object):
  """Cloud Bare Metal Solution client."""

  def __init__(self, api_version=_DEFAULT_API_VERSION):
    self._client = apis.GetClientInstance('baremetalsolution', api_version)
    self._v1_client = apis.GetClientInstance('baremetalsolution',
                                             _V1_API_VERSION)
    self._messages = apis.GetMessagesModule('baremetalsolution', api_version)
    self.instances_service = self._client.projects_locations_instances
    self.volumes_service = self._client.projects_locations_volumes
    self.snapshot_schedule_policies_service = self._client.projects_locations_snapshotSchedulePolicies
    self.snapshots_service = self._client.projects_locations_volumes_snapshots
    self.networks_service = self._client.projects_locations_networks
    self.locations_service = self._client.projects_locations
    self.luns_service = self._client.projects_locations_volumes_luns
    self.nfs_shares_service = self._client.projects_locations_nfsShares
    self.ssh_keys_service = self._client.projects_locations_sshKeys
    self.operation_service = self._client.projects_locations_operations
    self.os_images_service = self._client.projects_locations_osImages
    self.nfs_mount_permissions_str_to_message = {
        'READ_ONLY':
            self.messages.AllowedClient.MountPermissionsValueValuesEnum.READ,
        'READ_WRITE':
            self.messages.AllowedClient.MountPermissionsValueValuesEnum
            .READ_WRITE,
    }
    self.nfs_storage_type_str_to_message = {
        'SSD': self.messages.NfsShare.StorageTypeValueValuesEnum.SSD,
        'HDD': self.messages.NfsShare.StorageTypeValueValuesEnum.HDD,
    }

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._messages

  def GetInstance(self, resource):
    request = self.messages.BaremetalsolutionProjectsLocationsInstancesGetRequest(
        name=resource.RelativeName())
    return self.instances_service.Get(request)

  def ListInstances(self, parent, limit=None, page_size=None):
    request = self.messages.BaremetalsolutionProjectsLocationsInstancesListRequest(
        parent=parent)
    return list_pager.YieldFromList(
        self.instances_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='instances')

  def UpdateInstance(self, instance_resource, labels, os_image,
                     enable_hyperthreading, ssh_keys, kms_key_version,
                     clear_ssh_keys):
    """Update an existing instance resource."""
    updated_fields = []
    if labels is not None:
      updated_fields.append('labels')
    if os_image is not None:
      updated_fields.append('os_image')
    if enable_hyperthreading is not None:
      updated_fields.append('hyperthreading_enabled')
    if ssh_keys or clear_ssh_keys:
      updated_fields.append('ssh_keys')
    if kms_key_version is not None:
      updated_fields.append('kms_key_version')

    ssh_keys_relative = [ssh_key.RelativeName() for ssh_key in ssh_keys]

    instance_msg = self.messages.Instance(
        name=instance_resource.RelativeName(), labels=labels, osImage=os_image,
        hyperthreadingEnabled=enable_hyperthreading, sshKeys=ssh_keys_relative,
        kmsKeyVersion=kms_key_version)

    request = self.messages.BaremetalsolutionProjectsLocationsInstancesPatchRequest(
        name=instance_resource.RelativeName(),
        instance=instance_msg,
        updateMask=','.join(updated_fields))
    return self.instances_service.Patch(request)

  def RenameInstance(self, instance_resource, new_name):
    """Rename an existing instance resource."""
    rename_instance_request = self.messages.RenameInstanceRequest(
        newInstanceId=new_name)
    request = (
        self.messages.BaremetalsolutionProjectsLocationsInstancesRenameRequest(
            name=instance_resource.RelativeName(),
            renameInstanceRequest=rename_instance_request)
    )
    return self.instances_service.Rename(request)

  def LoadInstanceAuthInfo(self, instance_resource):
    """Load instance auth info."""
    request = self.messages.BaremetalsolutionProjectsLocationsInstancesLoadAuthInfoRequest(
        name=instance_resource.RelativeName())
    return self.instances_service.LoadAuthInfo(request)

  def ListSnapshotSchedulePolicies(self,
                                   project_resource,
                                   limit=None,
                                   page_size=None):
    parent = 'projects/%s/locations/global' % project_resource
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsSnapshotSchedulePoliciesListRequest(
            parent=parent))
    return list_pager.YieldFromList(
        self.snapshot_schedule_policies_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='snapshotSchedulePolicies')

  def GetSnapshotSchedulePolicy(self, resource):
    request = self.messages.BaremetalsolutionProjectsLocationsSnapshotSchedulePoliciesGetRequest(
        name=resource.RelativeName())
    return self.snapshot_schedule_policies_service.Get(request)

  def CreateSnapshotSchedulePolicy(self,
                                   policy_resource,
                                   labels,
                                   description,
                                   schedules):
    """Sends request to create a new Snapshot Schedule Policy."""
    policy_id = policy_resource.Name()
    parent = policy_resource.Parent().RelativeName()
    schedule_msgs = self._ParseSnapshotSchedules(schedules)
    policy_msg = self.messages.SnapshotSchedulePolicy(
        description=description,
        schedules=schedule_msgs,
        labels=labels)
    request = self.messages.BaremetalsolutionProjectsLocationsSnapshotSchedulePoliciesCreateRequest(
        parent=parent,
        snapshotSchedulePolicyId=policy_id,
        snapshotSchedulePolicy=policy_msg)
    return self.snapshot_schedule_policies_service.Create(request)

  def UpdateSnapshotSchedulePolicy(self,
                                   policy_resource,
                                   description,
                                   labels,
                                   schedules):
    """Sends request to update an existing SnapshotSchedulePolicy."""
    updated_fields = []
    if description:
      updated_fields.append('description')
    if labels is not None:
      updated_fields.append('labels')
    schedule_msgs = self._ParseSnapshotSchedules(schedules)
    if schedule_msgs:
      updated_fields.append('schedules')

    update_mask = ','.join(updated_fields)
    policy_msg = self.messages.SnapshotSchedulePolicy(
        description=description,
        schedules=schedule_msgs,
        labels=labels)
    request = self.messages.BaremetalsolutionProjectsLocationsSnapshotSchedulePoliciesPatchRequest(
        name=policy_resource.RelativeName(),
        snapshotSchedulePolicy=policy_msg,
        updateMask=update_mask)
    return self.snapshot_schedule_policies_service.Patch(request)

  def _ParseSnapshotSchedules(self, schedules):
    """Parses schedule ArgDict dicts into a list of Schedule messages."""
    schedule_msgs = []
    if schedules:
      for schedule_arg in schedules:
        schedule_msgs.append(self.messages.Schedule(
            crontabSpec=schedule_arg['crontab_spec'],
            retentionCount=schedule_arg['retention_count'],
            prefix=schedule_arg['prefix']))
    return schedule_msgs

  def DeleteSnapshotSchedulePolicy(self, resource):
    request = self.messages.BaremetalsolutionProjectsLocationsSnapshotSchedulePoliciesDeleteRequest(
        name=resource.RelativeName())
    return self.snapshot_schedule_policies_service.Delete(request)

  def ListVolumes(self,
                  parent,
                  limit=None,
                  page_size=None):
    request = self.messages.BaremetalsolutionProjectsLocationsVolumesListRequest(
        parent=parent)
    return list_pager.YieldFromList(
        self.volumes_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='volumes')

  def UpdateVolume(self,
                   volume_resource,
                   labels,
                   snapshot_schedule_policy_resource,
                   remove_snapshot_schedule_policy,
                   snapshot_auto_delete):
    """Update an existing volume resource."""
    updated_fields = []
    policy_name = None
    if snapshot_schedule_policy_resource:
      updated_fields.append('snapshotSchedulePolicy')
      policy_name = snapshot_schedule_policy_resource.RelativeName()
    elif remove_snapshot_schedule_policy:
      updated_fields.append('snapshotSchedulePolicy')
    if labels is not None:
      updated_fields.append('labels')
    if snapshot_auto_delete:
      updated_fields.append('snapshotAutoDeleteBehavior')

    volume_msg = self.messages.Volume(
        name=volume_resource.RelativeName(),
        snapshotAutoDeleteBehavior=snapshot_auto_delete,
        snapshotSchedulePolicy=policy_name,
        labels=labels)

    request = self.messages.BaremetalsolutionProjectsLocationsVolumesPatchRequest(
        name=volume_resource.RelativeName(),
        volume=volume_msg,
        updateMask=','.join(updated_fields))

    return self.volumes_service.Patch(request)

  def GetVolume(self, resource):
    request = self.messages.BaremetalsolutionProjectsLocationsVolumesGetRequest(
        name=resource.RelativeName())
    return self.volumes_service.Get(request)

  def RenameVolume(self, volume_resource, new_name):
    """Rename an existing volume resource."""
    rename_volume_request = self.messages.RenameVolumeRequest(
        newVolumeId=new_name)
    request = (
        self.messages.BaremetalsolutionProjectsLocationsVolumesRenameRequest(
            name=volume_resource.RelativeName(),
            renameVolumeRequest=rename_volume_request)
    )
    return self.volumes_service.Rename(request)

  def ListNetworks(self,
                   parent,
                   limit=None,
                   page_size=None):
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsNetworksListRequest(
            parent=parent))
    return list_pager.YieldFromList(
        self.networks_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='networks')

  def ListOSImages(self,
                   project_resource,
                   limit=None,
                   page_size=None):
    parent = 'projects/%s/locations/global' % project_resource
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsOsImagesListRequest(
            parent=parent))
    return list_pager.YieldFromList(
        self.os_images_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='osImages')

  def GetOSImage(self, resource):
    request = (
        self.messages.BaremetalsolutionProjectsLocationsOsImagesGetRequest(
            name=resource.RelativeName()))
    return self.os_images_service.Get(request)

  def GetNetwork(self, resource):
    request = (
        self.messages.BaremetalsolutionProjectsLocationsNetworksGetRequest(
            name=resource.RelativeName()))
    return self.networks_service.Get(request)

  def UpdateNetwork(self, network_resource, labels, ip_reservations):
    """Update an existing network resource."""
    updated_fields = []
    ip_reservations_messages = []
    if labels is not None:
      updated_fields.append('labels')
    if ip_reservations is not None:
      updated_fields.append('reservations')
      for ip_reservation in ip_reservations:
        ip_reservations_messages.append(self.messages.NetworkAddressReservation(
            startAddress=ip_reservation.start_address,
            endAddress=ip_reservation.end_address,
            note=ip_reservation.note,
            ))

    network_msg = self.messages.Network(
        name=network_resource.RelativeName(), labels=labels,
        reservations=ip_reservations_messages)

    request = self.messages.BaremetalsolutionProjectsLocationsNetworksPatchRequest(
        name=network_resource.RelativeName(),
        network=network_msg,
        updateMask=','.join(updated_fields))

    return self.networks_service.Patch(request)

  def RenameNetwork(self, network_resource, new_name):
    """Rename an existing network resource."""
    rename_network_request = self.messages.RenameNetworkRequest(
        newNetworkId=new_name)
    request = (
        self.messages.BaremetalsolutionProjectsLocationsNetworksRenameRequest(
            name=network_resource.RelativeName(),
            renameNetworkRequest=rename_network_request)
    )
    return self.networks_service.Rename(request)

  def IsClientNetwork(self, network):
    return network.type == self.messages.Network.TypeValueValuesEnum.CLIENT

  def IsPrivateNetwork(self, network):
    return network.type == self.messages.Network.TypeValueValuesEnum.PRIVATE

  def IsClientLogicalNetworkInterface(self, logical_network_interface):
    return logical_network_interface.networkType == self.messages.LogicalNetworkInterface.NetworkTypeValueValuesEnum.CLIENT

  def IsPrivateLogicalNetworkInterface(self, logical_network_interface):
    return logical_network_interface.networkType == self.messages.LogicalNetworkInterface.NetworkTypeValueValuesEnum.PRIVATE

  def ListLUNsForVolume(self, volume_resource, limit=None,
                        page_size=None):
    parent = volume_resource.RelativeName()
    request = (self.messages
               .BaremetalsolutionProjectsLocationsVolumesLunsListRequest(
                   parent=parent))
    return list_pager.YieldFromList(
        self.luns_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='luns')

  def GetLUN(self, resource):
    request = (self.messages
               .BaremetalsolutionProjectsLocationsVolumesLunsGetRequest(
                   name=resource.RelativeName()))
    return self.luns_service.Get(request)

  def ListSnapshotsForVolume(self,
                             volume_resource,
                             limit=None,
                             page_size=None):
    parent = volume_resource.RelativeName()
    request = (self.messages
               .BaremetalsolutionProjectsLocationsVolumesSnapshotsListRequest(
                   parent=parent))
    return list_pager.YieldFromList(
        self.snapshots_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='volumeSnapshots')

  def GetVolumeSnapshot(self, resource):
    request = (self.messages
               .BaremetalsolutionProjectsLocationsVolumesSnapshotsGetRequest(
                   name=resource.RelativeName()))
    return self.snapshots_service.Get(request)

  def CreateVolumeSnapshot(self, resource, name, description):
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsVolumesSnapshotsCreateRequest(
            parent=resource.RelativeName(),
            volumeSnapshot=self.messages.VolumeSnapshot(
                name=name, description=description)))
    return self.snapshots_service.Create(request)

  def DeleteVolumeSnapshot(self, resource):
    request = (self.messages
               .BaremetalsolutionProjectsLocationsVolumesSnapshotsDeleteRequest(
                   name=resource.RelativeName()))
    return self.snapshots_service.Delete(request)

  def RestoreVolumeSnapshot(self, snapshot_name):
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsVolumesSnapshotsRestoreVolumeSnapshotRequest(  # pylint: disable=line-too-long
            volumeSnapshot=snapshot_name))
    return self.snapshots_service.RestoreVolumeSnapshot(request)

  def GetNfsShare(self, resource):
    request = self.messages.BaremetalsolutionProjectsLocationsNfsSharesGetRequest(
        name=resource.RelativeName())
    return self.nfs_shares_service.Get(request)

  def ListNfsShares(self,
                    parent,
                    limit=None,
                    page_size=None):
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsNfsSharesListRequest(
            parent=parent))
    return list_pager.YieldFromList(
        self.nfs_shares_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='nfsShares')

  def UpdateNfsShare(self, nfs_share_resource, labels, allowed_clients):
    """Update an existing nfs share resource."""
    updated_fields = []
    updated_allowed_clients = []
    if labels is not None:
      updated_fields.append('labels')
    if allowed_clients is not None:
      updated_fields.append('allowedClients')
      updated_allowed_clients = allowed_clients

    nfs_share_msg = self.messages.NfsShare(
        name=nfs_share_resource.RelativeName(), labels=labels,
        allowedClients=updated_allowed_clients)

    request = self.messages.BaremetalsolutionProjectsLocationsNfsSharesPatchRequest(
        name=nfs_share_resource.RelativeName(),
        nfsShare=nfs_share_msg,
        updateMask=','.join(updated_fields))

    return self.nfs_shares_service.Patch(request)

  def DeleteNfsShare(self, nfs_share_resource):
    """Delete an existing nfs share resource."""
    request = self.messages.BaremetalsolutionProjectsLocationsNfsSharesDeleteRequest(
        name=nfs_share_resource.RelativeName())
    return self.nfs_shares_service.Delete(request)

  def CreateNfsShare(self,
                     nfs_share_resource,
                     size_gib,
                     storage_type,
                     allowed_clients_dicts,
                     labels):
    """Create an NFS share resource."""
    allowed_clients = self.ParseAllowedClientsDicts(
        nfs_share_resource=nfs_share_resource,
        allowed_clients_dicts=allowed_clients_dicts)
    nfs_share_msg = self.messages.NfsShare(
        name=nfs_share_resource.RelativeName(),
        requestedSizeGib=size_gib,
        storageType=self.nfs_storage_type_str_to_message[storage_type],
        allowedClients=allowed_clients,
        labels=labels)
    request = self.messages.BaremetalsolutionProjectsLocationsNfsSharesCreateRequest(
        nfsShare=nfs_share_msg,
        parent=nfs_share_resource.Parent().RelativeName())
    return self.nfs_shares_service.Create(request)

  def RenameNfsShare(self, nfs_share_resource, new_name):
    """Rename an existing nfs share resource."""
    rename_nfs_share_request = self.messages.RenameNfsShareRequest(
        newNfsshareId=new_name)
    request = (
        self.messages.BaremetalsolutionProjectsLocationsNfsSharesRenameRequest(
            name=nfs_share_resource.RelativeName(),
            renameNfsShareRequest=rename_nfs_share_request)
    )
    return self.nfs_shares_service.Rename(request)

  def ListSshKeys(self,
                  project_resource,
                  limit=None,
                  page_size=None):
    parent = 'projects/%s/locations/global' % project_resource
    request = (
        self.messages
        .BaremetalsolutionProjectsLocationsSshKeysListRequest(
            parent=parent))
    return list_pager.YieldFromList(
        self.ssh_keys_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='sshKeys')

  def CreateSshKey(self,
                   resource,
                   public_key):
    """Sends request to create an SSH key."""
    request = self.messages.BaremetalsolutionProjectsLocationsSshKeysCreateRequest(
        parent=resource.Parent().RelativeName(),
        sshKeyId=resource.Name(),
        sSHKey=self.messages.SSHKey(publicKey=public_key))
    return self.ssh_keys_service.Create(request)

  def DeleteSshKey(self, resource):
    request = self.messages.BaremetalsolutionProjectsLocationsSshKeysDeleteRequest(
        name=resource.RelativeName())
    return self.ssh_keys_service.Delete(request)

  def ParseAllowedClientsDicts(self, nfs_share_resource, allowed_clients_dicts):
    """Parses NFS share allowed client list of dicts."""
    allowed_clients = []
    for allowed_client in allowed_clients_dicts:
      mount_permissions = self.nfs_mount_permissions_str_to_message[
          allowed_client['mount-permissions']]
      network_full_name = util.NFSNetworkFullName(
          nfs_share_resource=nfs_share_resource,
          allowed_client_dict=allowed_client)
      allowed_clients.append(
          self.messages.AllowedClient(
              network=network_full_name,
              allowedClientsCidr=allowed_client['cidr'],
              mountPermissions=mount_permissions,
              allowDev=allowed_client['allow-dev'],
              allowSuid=allowed_client['allow-suid'],
              noRootSquash=not allowed_client['enable-root-squash'],
              )
          )
    return allowed_clients

