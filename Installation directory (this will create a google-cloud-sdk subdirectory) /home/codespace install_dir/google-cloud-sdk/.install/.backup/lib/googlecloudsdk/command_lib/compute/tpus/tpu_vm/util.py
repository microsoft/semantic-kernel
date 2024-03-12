# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""CLI Utilities for Cloud TPU VM commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

import six


class NoFieldsSpecifiedError(exceptions.Error):
  """Error if no fields are specified for an update request."""


class AttachDiskError(exceptions.Error):
  """Error if the update request is invalid for attaching a disk."""


class DetachDiskError(exceptions.Error):
  """Error if the update request is invalid for detaching a disk."""


class BootDiskConfigurationError(exceptions.Error):
  """Error if the boot disk configuration is invalid."""


def GetProject(release_track, ssh_helper):
  holder = base_classes.ComputeApiHolder(release_track)
  project_name = properties.VALUES.core.project.GetOrFail()
  return ssh_helper.GetProject(holder.client, project_name)


def InvertBoolean(boolean):
  """Inverts the boolean value passed in."""
  return not boolean


def MergeMetadata(api_version='v2'):
  """Request hook for merging the metadata and metadata from file."""

  def Process(unused_ref, args, request):
    """Request hook for merging the metadata and metadata from file.

    Args:
      unused_ref: ref to the service.
      args:  The args for this method.
      request: The request to be made.

    Returns:
      Request with metadata field populated.
    """
    metadata_dict = metadata_utils.ConstructMetadataDict(
        args.metadata, args.metadata_from_file)
    tpu_messages = GetMessagesModule(version=api_version)
    if request.node.metadata is None:
      request.node.metadata = tpu_messages.Node.MetadataValue()
    for key, value in six.iteritems(metadata_dict):
      request.node.metadata.additionalProperties.append(
          tpu_messages.Node.MetadataValue.AdditionalProperty(
              key=key, value=value))
    return request

  return Process


def GetTagsUpdateFromArgs(args, tags):
  """Generate the change to the tags on a resource based on the arguments.

  Args:
    args: The args for this method.
    tags: The current list of tags.

  Returns:
    The change to the tags after all of the arguments are applied.
  """
  tags_update = tags
  if args.IsKnownAndSpecified('clear_tags'):
    tags_update = []
  if args.IsKnownAndSpecified('add_tags'):
    tags_update = sorted(set(tags_update + args.add_tags))
  if args.IsKnownAndSpecified('remove_tags'):
    tags_update = sorted(set(tags_update) - set(args.remove_tags))
  return tags_update


def GenerateUpdateMask(api_version='v2'):
  """Request hook for constructing the updateMask for update requests."""

  def Process(unused_ref, args, request):
    """Request hook for constructing the updateMask for update requests.

    Args:
      unused_ref: ref to the service.
      args: The args for this method.
      request: The request to be made.

    Returns:
      Request with updateMask field populated.

    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
      AttachDiskError: if the request for attaching a disk is invalid.
      DetachDiskError: if the request for detaching a disk is invalid.
    """

    update_mask = set()
    tpu_messages = GetMessagesModule(version=api_version)

    # Since it's possible that different API versions support different flags,
    # we must check that the flag is both known in this version and if it is
    # specified.
    if args.IsKnownAndSpecified('description'):
      update_mask.add('description')

    if args.IsKnownAndSpecified('internal_ips'):
      update_mask.add('network_config.enable_external_ips')

    if (args.IsKnownAndSpecified('update_labels') or
        args.IsKnownAndSpecified('remove_labels') or
        args.IsKnownAndSpecified('clear_labels')):
      labels_diff = labels_util.Diff.FromUpdateArgs(args)
      if labels_diff.MayHaveUpdates():
        labels_update = labels_diff.Apply(
            tpu_messages.Node.LabelsValue,
            request.node.labels)
        if labels_update.needs_update:
          request.node.labels = labels_update.labels
          update_mask.add('labels')

    if (args.IsKnownAndSpecified('add_tags') or
        args.IsKnownAndSpecified('remove_tags') or
        args.IsKnownAndSpecified('clear_tags')):
      tags_update = GetTagsUpdateFromArgs(args, request.node.tags)
      if set(tags_update) != set(request.node.tags):
        request.node.tags = tags_update
        update_mask.add('tags')

    if args.IsKnownAndSpecified('metadata_from_file'):
      metadata_dict = metadata_utils.ConstructMetadataDict(
          None, args.metadata_from_file)
      request.node.metadata = tpu_messages.Node.MetadataValue()
      for key, value in six.iteritems(metadata_dict):
        request.node.metadata.additionalProperties.append(
            tpu_messages.Node.MetadataValue.AdditionalProperty(
                key=key, value=value))
      update_mask.add('metadata')
    elif (args.IsKnownAndSpecified('update_metadata') or
          args.IsKnownAndSpecified('remove_metadata') or
          args.IsKnownAndSpecified('clear_metadata')):
      metadata_dict = {}
      if request.node.metadata is not None:
        for item in request.node.metadata.additionalProperties:
          metadata_dict[item.key] = item.value
      # Apply flags one by one since we allow multiple flags to be set at once.
      # The order should match the flags' descriptions.
      metadata_update = map_util.ApplyMapFlags(metadata_dict, None,
                                               None, args.clear_metadata, None,
                                               None)
      metadata_update = map_util.ApplyMapFlags(metadata_update, None,
                                               args.update_metadata, None, None,
                                               None)
      metadata_update = map_util.ApplyMapFlags(metadata_update, None, None,
                                               None, args.remove_metadata, None)
      request.node.metadata = tpu_messages.Node.MetadataValue()
      for key, value in six.iteritems(metadata_update):
        request.node.metadata.additionalProperties.append(
            tpu_messages.Node.MetadataValue.AdditionalProperty(
                key=key, value=value))
      update_mask.add('metadata')

    if args.IsKnownAndSpecified('attach_disk'):
      mode, source = '', ''
      for key in args.attach_disk.keys():
        if key == 'mode':
          mode = args.attach_disk['mode']
        elif key == 'source':
          source = args.attach_disk['source']
        else:
          raise AttachDiskError(
              'argument --attach-disk: valid keys are [mode, source]; '
              'received: ' + key
          )
      if mode == 'read-only':
        mode_enum = tpu_messages.AttachedDisk.ModeValueValuesEnum.READ_ONLY
      elif not mode or mode == 'read-write':
        mode_enum = tpu_messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE
      else:
        raise AttachDiskError(
            'argument --attach-disk: key mode: can only attach disks in '
            'read-write or read-only mode; received: ' + mode
        )
      disk_to_attach = tpu_messages.AttachedDisk(
          mode=mode_enum,
          sourceDisk=source
      )
      request.node.dataDisks.append(disk_to_attach)
      update_mask.add('data_disks')

    elif args.IsKnownAndSpecified('detach_disk'):
      if not request.node.dataDisks:
        raise DetachDiskError(
            'argument --detach-disk: No data disks to detach from current TPU '
            'VM.'
        )
      source_disk_list = []
      for disk in request.node.dataDisks:
        source_disk_list.append(disk.sourceDisk)
      for i, source_disk in enumerate(source_disk_list):
        if args.detach_disk != source_disk:
          continue
        if args.detach_disk == source_disk:
          del request.node.dataDisks[i]
          break
      else:
        raise DetachDiskError(
            'argument --detach-disk: The specified data disk '
            + args.detach_disk + ' is not currently attached to the TPU VM.'
        )
      update_mask.add('data_disks')

    if not update_mask:
      raise NoFieldsSpecifiedError(
          'No fields would change as a result of this update; must specify at '
          'least one field to update.')

    request.updateMask = ','.join(update_mask)
    return request

  return Process


def RemoveConflictingDefaults(unused_ref, args, request):
  """Unset acceleratorType flag when it conflicts with topology arguments.

  Args:
    unused_ref: ref to the service.
    args:  The args for this method.
    request: The request to be made.

  Returns:
    Request with metadata field populated.
  """
  if args.topology is not None:
    request.node.acceleratorType = None
  return request


def GetMessagesModule(version='v2'):
  return apis.GetMessagesModule('tpu', version)


def StartRequestHook(api_version='v2'):
  """Declarative request hook for TPU Start command."""

  def Process(ref, args, request):
    del ref
    del args
    start_request = GetMessagesModule(version=api_version).StartNodeRequest()
    request.startNodeRequest = start_request
    return request

  return Process


def StopRequestHook(api_version='v2'):
  """Declarative request hook for TPU Stop command."""

  def Process(ref, args, request):
    del ref
    del args
    stop_request = GetMessagesModule(version=api_version).StopNodeRequest()
    request.stopNodeRequest = stop_request
    return request

  return Process


def IsTPUVMNode(node):
  api_version = six.text_type(node.apiVersion).upper()
  return (not api_version.startswith('V1')
          and api_version != 'API_VERSION_UNSPECIFIED')


def FilterTPUVMNodes(response, args):
  """Removes Cloud TPU V1 API nodes from the 'list' output.

  Used with 'compute tpus tpu-vm list'.

  Args:
    response: response to ListNodes.
    args: the arguments for the list command.

  Returns:
    A response with only TPU VM (non-V1 API) nodes.
  """
  del args
  return list(six.moves.filter(IsTPUVMNode, response))


class GuestAttributesListEntry(object):
  """Holder for GetGuestAttributes output."""

  def __init__(self, worker_id, namespace, key, value):
    self.worker_id = worker_id
    self.namespace = namespace
    self.key = key
    self.value = value


def TransformGuestAttributes(response, args):
  """Transforms the GuestAttributes into a flatter list.

  This is needed to make clearer output in the case of TPU pods, since they have
  many workers.

  Args:
    response: response to GetGuestAttributes.
    args: the arguments for the GetGuestAttributes command.

  Returns:
    A list of GuestAttributesListEntry objects.
  """
  del args
  lst = []
  for i, ga in enumerate(response.guestAttributes):
    for entry in ga.queryValue.items:
      lst.append(
          GuestAttributesListEntry(i, entry.namespace, entry.key, entry.value))
  return lst


def CheckTPUVMNode(response, args):
  """Verifies that the node is a TPU VM node.

  If it is not a TPU VM node, exit with an error instead.

  Args:
    response: response to GetNode.
    args: the arguments for the list command.

  Returns:
    The response to GetNode if the node is TPU VM.
  """
  del args
  if IsTPUVMNode(response):
    return response
  log.err.Print('ERROR: Please use "gcloud compute tpus describe" for Cloud TPU'
                ' nodes that are not TPU VM.')
  sys.exit(1)


def ParseBootDiskConfigurations(api_version='v2'):
  """Request hook for parsing boot disk configurations."""

  def Process(unused_ref, args, request):
    """Parses configurations for boot disk.

    Parsing boot disk configuration if --boot-disk flag is set.

    Args:
      unused_ref: ref to the service.
      args:  The args for this method.
      request: The request to be made.

    Returns:
      Request with boot disk configuration fields populated.

    Raises:
      BootDiskConfigurationError: if confidential compute is enable
        but kms-key is not provided.
      BootDiskConfigurationError: if invalid argument name is provided.
    """
    if not args or not args.IsKnownAndSpecified('boot_disk'):
      return request

    kms_key_arg_name = 'kms-key'
    confidential_compute_arg_name = 'confidential-compute'
    for arg_name in args.boot_disk.keys():
      if arg_name not in [kms_key_arg_name, confidential_compute_arg_name]:
        raise BootDiskConfigurationError(
            '--boot-disk only supports arguments: %s and %s'
            % (confidential_compute_arg_name, kms_key_arg_name)
        )

    tpu_messages = GetMessagesModule(version=api_version)
    enable_confidential_compute = args.boot_disk.get(
        confidential_compute_arg_name, 'False').lower() == 'true'
    kms_key = args.boot_disk.get(kms_key_arg_name, None)

    if enable_confidential_compute and kms_key is None:
      raise BootDiskConfigurationError(
          'argument --boot-disk: with confidential-compute=%s '
          'requires kms-key; received: %s' % (
              enable_confidential_compute, kms_key)
      )
    customer_encryption_key = tpu_messages.CustomerEncryptionKey(
        kmsKeyName=kms_key
    )
    request.node.bootDiskConfig = tpu_messages.BootDiskConfig(
        customerEncryptionKey=customer_encryption_key,
        enableConfidentialCompute=enable_confidential_compute,
    )
    return request

  return Process


class TPUNode(object):
  """Helper to create and modify TPU nodes."""

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
    """Retrieves the TPU node in the given zone."""
    project = properties.VALUES.core.project.Get(required=True)
    fully_qualified_node_name_ref = resources.REGISTRY.Parse(
        name,
        params={
            'locationsId': zone,
            'projectsId': project
        },
        collection='tpu.projects.locations.nodes',
        )
    request = self.messages.TpuProjectsLocationsNodesGetRequest(
        name=fully_qualified_node_name_ref.RelativeName())
    return self.client.projects_locations_nodes.Get(request)

  def GetGuestAttributes(self, name, zone, worker_id=''):
    """Retrives the Guest Attributes for the nodes."""
    project = properties.VALUES.core.project.Get(required=True)
    fully_qualified_node_name_ref = resources.REGISTRY.Parse(
        name,
        params={
            'locationsId': zone,
            'projectsId': project
        },
        collection='tpu.projects.locations.nodes',
        )
    get_guest_attributes_request = self.messages.GetGuestAttributesRequest(
        workerIds=[worker_id])
    request = self.messages.TpuProjectsLocationsNodesGetGuestAttributesRequest(
        name=fully_qualified_node_name_ref.RelativeName(),
        getGuestAttributesRequest=get_guest_attributes_request)
    return self.client.projects_locations_nodes.GetGuestAttributes(request)

  def UpdateNode(self, name, zone, node, update_mask, poller_message):
    """Updates the TPU node in the given zone."""
    project = properties.VALUES.core.project.Get(required=True)
    fully_qualified_node_name_ref = resources.REGISTRY.Parse(
        name,
        params={
            'locationsId': zone,
            'projectsId': project
        },
        collection='tpu.projects.locations.nodes',
        )
    request = self.messages.TpuProjectsLocationsNodesPatchRequest(
        name=fully_qualified_node_name_ref.RelativeName(),
        node=node,
        updateMask=update_mask)

    # Call UpdateNode to start the LRO.
    operation = self.client.projects_locations_nodes.Patch(request)
    operation_ref = resources.REGISTRY.ParseRelativeName(
        operation.name, collection='tpu.projects.locations.operations'
    )
    # Wait for the UpdateNode LRO to complete.
    return self.WaitForOperation(operation_ref, poller_message)

  def UpdateMetadataKey(self, metadata, key, value):
    """Updates a key in the TPU metadata object.

    If the key does not exist, it is added.

    Args:
      metadata: tpu.messages.Node.MetadataValue, the TPU's metadata.
      key: str, the key to be updated.
      value: str, the new value for the key.

    Returns:
      The updated metadata.
    """
    # If the metadata is empty, return a new metadata object with just the key.
    if metadata is None or metadata.additionalProperties is None:
      return self.messages.Node.MetadataValue(
          additionalProperties=[
              self.messages.Node.MetadataValue.AdditionalProperty(
                  key=key, value=value)])

    item = None
    for x in metadata.additionalProperties:
      if x.key == key:
        item = x
        break
    if item is not None:
      item.value = value
    else:
      # The key is not in the metadata, so append it.
      metadata.additionalProperties.append(
          self.messages.Node.MetadataValue.AdditionalProperty(
              key=key, value=value))
    return metadata

  def WaitForOperation(self, operation_ref, message):
    operation_poller = waiter.CloudOperationPoller(
        self.client.projects_locations_nodes,
        self.client.projects_locations_operations)
    return waiter.WaitFor(operation_poller, operation_ref, message)


class SSHPreppedNode(object):
  """Object that has all the data needed to successfully SSH into a node.

  Attributes:
    worker_ips: The IPs of the workers of the node.
    ssh_helper: The ssh_helper used to SSH into the node.
    id: The id of the node.
    tpu_name: The unqualified TPU VM name.
    instance_names: The name of the instances of the workers of the node.
    project: The project associated with the node.
    command_list: The list of the commands passed into ssh.
    remainder: The remainder list of ssh_args used to pass into the SSH command.
    host_key_suffixes: The host key suffixes associated with the node.
    user: The user executing the SSH command.
    release_track: The release track for the SSH protos (Alpha, Beta, etc.).
    enable_batching: A bool indicating if the user enabled batching for the
      node.
  """

  def __init__(self, tpu_name, user, release_track, enable_batching):
    self.tpu_name = tpu_name
    self.user = user
    self.release_track = release_track
    self.enable_batching = enable_batching

    self.worker_ips = []
    self.ssh_helper = None
    self.id = None
    self.instance_names = []
    self.project = None
    self.command_list = []
    self.remainder = None
    self.host_key_suffixes = []


class SCPPreppedNode(SSHPreppedNode):
  """Object that has all the data needed to successfully SCP into a node.

  Attributes:
    srcs: The sources for SCP.
    dst: The destination for SCP.
  """

  def __init__(self, tpu_name, user, release_track, enable_batching, srcs, dst):
    super(SCPPreppedNode, self).__init__(
        tpu_name, user, release_track, enable_batching
    )

    self.srcs = srcs
    self.dst = dst
