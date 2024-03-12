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
"""Utility file that contains helpers for Queued Resources."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as sdk_core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times
import six


class BootDiskConfigurationError(sdk_core_exceptions.Error):
  """Error if the boot disk configuration is invalid."""


def GetMessagesModule(version):
  return apis.GetMessagesModule('tpu', version)


# TODO(b/276933950) Consider merging this MergeMetadata with
# googlecloudsdk.command_lib.compute.tpus.tpu_vm.util.MergeMetadata by moving
# it to googlecloudsdk.command_lib.compute.tpus.util
def MergeMetadata(args, api_version):
  """Creates the metadata for the Node.

  Based on googlecloudsdk.command_lib.compute.tpus.tpu_vm.util.MergeMetadata.

  Args:
    args:  The gcloud args
    api_version: The api version (e.g. v2 or v2alpha1)

  Returns:
    The constructed MetadataValue.
  """
  metadata_dict = metadata_utils.ConstructMetadataDict(
      args.metadata, args.metadata_from_file
  )
  tpu_messages = GetMessagesModule(api_version)
  metadata = tpu_messages.Node.MetadataValue()
  for key, value in six.iteritems(metadata_dict):
    metadata.additionalProperties.append(
        tpu_messages.Node.MetadataValue.AdditionalProperty(key=key, value=value)
    )
  return metadata


def CreateNodeSpec(api_version):
  """Creates the repeated structure nodeSpec from args."""

  def Process(ref, args, request):
    tpu_messages = GetMessagesModule(api_version)
    if request.queuedResource is None:
      request.queuedResource = tpu_messages.QueuedResource()
    if request.queuedResource.tpu is None:
      request.queuedResource.tpu = tpu_messages.Tpu()

    if request.queuedResource.tpu.nodeSpec:
      node_spec = request.queuedResource.tpu.nodeSpec[0]
    else:
      request.queuedResource.tpu.nodeSpec = []
      node_spec = tpu_messages.NodeSpec()
      node_spec.node = tpu_messages.Node()

    node_spec.parent = ref.Parent().RelativeName()

    if args.accelerator_type:
      node_spec.node.acceleratorType = args.accelerator_type

    node_spec.node.runtimeVersion = args.runtime_version
    if args.data_disk:
      node_spec.node.dataDisks = []
      for data_disk in args.data_disk:
        attached_disk = tpu_messages.AttachedDisk(
            sourceDisk=data_disk.sourceDisk, mode=data_disk.mode
        )
        node_spec.node.dataDisks.append(attached_disk)
    if args.description:
      node_spec.node.description = args.description
    if args.labels:
      node_spec.node.labels = tpu_messages.Node.LabelsValue()
      node_spec.node.labels.additionalProperties = []
      for key, value in args.labels.items():
        node_spec.node.labels.additionalProperties.append(
            tpu_messages.Node.LabelsValue.AdditionalProperty(
                key=key, value=value
            )
        )
    if args.range:
      node_spec.node.cidrBlock = args.range
    if args.shielded_secure_boot:
      node_spec.node.shieldedInstanceConfig = (
          tpu_messages.ShieldedInstanceConfig(enableSecureBoot=True)
      )
    if api_version == 'v2alpha1' and args.autocheckpoint_enabled:
      node_spec.node.autocheckpointEnabled = True

    node_spec.node.networkConfig = tpu_messages.NetworkConfig()
    node_spec.node.serviceAccount = tpu_messages.ServiceAccount()
    if args.network:
      node_spec.node.networkConfig.network = args.network
    if args.subnetwork:
      node_spec.node.networkConfig.subnetwork = args.subnetwork
    if args.service_account:
      node_spec.node.serviceAccount.email = args.service_account
    if args.scopes:
      node_spec.node.serviceAccount.scope = args.scopes
    if args.tags:
      node_spec.node.tags = args.tags
    node_spec.node.networkConfig.enableExternalIps = not args.internal_ips

    if api_version == 'v2alpha1' and args.boot_disk:
      node_spec.node.bootDiskConfig = ParseBootDiskConfig(args.boot_disk)

    node_spec.node.metadata = MergeMetadata(args, api_version)

    if args.node_prefix and not args.node_count:
      raise exceptions.ConflictingArgumentsException(
          'Can only specify --node-prefix if --node-count is also specified.'
      )

    if args.node_id:
      node_spec.nodeId = args.node_id
    elif args.node_count:
      if api_version == 'v2alpha1':
        node_spec.multiNodeParams = tpu_messages.MultiNodeParams()
        node_spec.multiNodeParams.nodeCount = args.node_count
        if args.node_prefix:
          node_spec.multiNodeParams.nodeIdPrefix = args.node_prefix
      else:  # For v2 API, MultiNodeParams was renamed to MultisliceParams
        node_spec.multisliceParams = tpu_messages.MultisliceParams()
        node_spec.multisliceParams.nodeCount = args.node_count
        if args.node_prefix:
          node_spec.multisliceParams.nodeIdPrefix = args.node_prefix
    request.queuedResource.tpu.nodeSpec = [node_spec]
    return request

  return Process


def ParseBootDiskConfig(
    boot_disk_args,
) -> GetMessagesModule('v2alpha1').BootDiskConfig:
  """Parses configurations for boot disk. Boot disk is only in v2alpha1 API.

  Parsing boot disk configuration if --boot-disk flag is set.

  Args:
    boot_disk_args: args for --boot-disk flag.

  Returns:
    Return GetMessagesModule().BootDiskConfig object with parsed configurations.

  Raises:
    BootDiskConfigurationError: if confidential compute is enable
      but kms-key is not provided.
    BootDiskConfigurationError: if invalid argument name is provided.
  """
  tpu_messages = GetMessagesModule('v2alpha1')
  kms_key_arg_name = 'kms-key'
  confidential_compute_arg_name = 'confidential-compute'
  for arg_name in boot_disk_args.keys():
    if arg_name not in [kms_key_arg_name, confidential_compute_arg_name]:
      raise BootDiskConfigurationError(
          '--boot-disk only supports arguments: %s and %s'
          % (confidential_compute_arg_name, kms_key_arg_name)
      )

  enable_confidential_compute = (
      boot_disk_args.get(confidential_compute_arg_name, 'False').lower()
      == 'true'
  )
  kms_key = boot_disk_args.get(kms_key_arg_name, None)

  if enable_confidential_compute and kms_key is None:
    raise BootDiskConfigurationError(
        'argument --boot-disk: with confidential-compute=%s '
        'requires kms-key; received: %s'
        % (enable_confidential_compute, kms_key)
    )
  customer_encryption_key = tpu_messages.CustomerEncryptionKey(
      kmsKeyName=kms_key
  )
  return tpu_messages.BootDiskConfig(
      customerEncryptionKey=customer_encryption_key,
      enableConfidentialCompute=enable_confidential_compute,
  )


def VerifyNodeCount(ref, args, request):
  del ref  # unused
  if args.node_count and args.node_count <= 1:
    raise exceptions.InvalidArgumentException(
        '--node-count', 'Node count must be greater than 1'
    )
  return request


def SetBestEffort(ref, args, request):
  """Creates an empty BestEffort structure if best-effort arg flag is set."""
  del ref  # unused
  if args.best_effort:
    tpu_messages = GetMessagesModule('v2alpha1')
    if request.queuedResource is None:
      request.queuedResource = tpu_messages.QueuedResource()
    if request.queuedResource.bestEffort is None:
      request.queuedResource.bestEffort = tpu_messages.BestEffort()

  return request


def SetSpot(api_version):
  """Creates an empty Spot structure if spot flag is set."""

  def Process(ref, args, request):
    del ref  # unused
    if args.spot:
      tpu_messages = GetMessagesModule(api_version)
      if request.queuedResource is None:
        request.queuedResource = tpu_messages.QueuedResource()
      if request.queuedResource.spot is None:
        request.queuedResource.spot = tpu_messages.Spot()

    return request

  return Process


def SetGuaranteed(api_version):
  """Creates an empty Guaranteed structure if arg flag is set."""

  def Process(ref, args, request):
    del ref  # unused
    if args.guaranteed:
      tpu_messages = GetMessagesModule(api_version)
      if request.queuedResource is None:
        request.queuedResource = tpu_messages.QueuedResource()
      if request.queuedResource.guaranteed is None:
        request.queuedResource.guaranteed = tpu_messages.Guaranteed()

    return request

  return Process


def SetValidInterval(api_version):
  """Combine multiple timing constraints into a valid_interval."""

  def Process(ref, args, request):
    del ref  # unused
    if (args.valid_after_duration and args.valid_after_time) or (
        args.valid_until_duration and args.valid_until_time
    ):
      raise exceptions.ConflictingArgumentsException(
          'Only one timing constraint for each of (start, end) time is'
          ' permitted'
      )
    tpu_messages = GetMessagesModule(api_version)
    current_time = times.Now()

    start_time = None
    if args.valid_after_time:
      start_time = args.valid_after_time
    elif args.valid_after_duration:
      start_time = args.valid_after_duration.GetRelativeDateTime(current_time)

    end_time = None
    if args.valid_until_time:
      end_time = args.valid_until_time
    elif args.valid_until_duration:
      end_time = args.valid_until_duration.GetRelativeDateTime(current_time)

    if start_time and end_time:
      valid_interval = tpu_messages.Interval()
      valid_interval.startTime = times.FormatDateTime(start_time)
      valid_interval.endTime = times.FormatDateTime(end_time)

      if request.queuedResource is None:
        request.queuedResource = tpu_messages.QueuedResource()
      # clear all other queueing policies
      request.queuedResource.queueingPolicy = tpu_messages.QueueingPolicy()
      request.queuedResource.queueingPolicy.validInterval = valid_interval
    return request

  return Process


def CreateReservationName(api_version):
  """Creates the target reservation name from args.

  Args:
    api_version: The api version (e.g. v2 or v2alpha1)

  Returns:
    Handler which sets request.queuedResource.reservationName
  """

  def Process(ref, args, request):
    del ref  # unused
    if (
        (args.reservation_host_project and args.reservation_host_folder)
        or (args.reservation_host_folder and args.reservation_host_organization)
        or (
            args.reservation_host_organization and args.reservation_host_project
        )
    ):
      raise exceptions.ConflictingArgumentsException(
          'Only one reservation host is permitted'
      )
    pattern = '{}/{}/locations/{}/reservations/-'
    reservation_name = None
    if args.reservation_host_project:
      reservation_name = pattern.format(
          'projects', args.reservation_host_project, args.zone
      )
    elif args.reservation_host_folder:
      reservation_name = pattern.format(
          'folders', args.reservation_host_folder, args.zone
      )
    elif args.reservation_host_organization:
      reservation_name = pattern.format(
          'organizations', args.reservation_host_organization, args.zone
      )
    elif api_version == 'v2' and hasattr(args, 'reserved') and args.reserved:
      project = properties.VALUES.core.project.GetOrFail()
      reservation_name = pattern.format('projects', project, args.zone)

    if reservation_name:
      request.queuedResource.reservationName = reservation_name
    return request

  return Process


def SetForce(ref, args, request):
  """Sets force arg to true if flag is set."""
  del ref  # unused
  if hasattr(args, 'force') and args.force:
    request.force = True

  return request


class TPUQueuedResource(object):
  """Helper to get TPU Queued Resources."""

  def __init__(self, release_track):
    if release_track == base.ReleaseTrack.ALPHA:
      self._api_version = 'v2alpha1'
    else:
      self._api_version = 'v2'

    self.client = apis.GetClientInstance('tpu', self._api_version)
    self.messages = apis.GetMessagesModule('tpu', self._api_version)

  def GetMessages(self):
    return self.messages

  def Get(self, name, zone):
    """Retrieves the Queued Resource in the given project and zone."""
    project = properties.VALUES.core.project.Get(required=True)
    fully_qualified_queued_resource_name_ref = resources.REGISTRY.Parse(
        name,
        params={'locationsId': zone, 'projectsId': project},
        collection='tpu.projects.locations.queuedResources',
        api_version=self._api_version,
    )
    request = self.messages.TpuProjectsLocationsQueuedResourcesGetRequest(
        name=fully_qualified_queued_resource_name_ref.RelativeName()
    )
    return self.client.projects_locations_queuedResources.Get(request)
