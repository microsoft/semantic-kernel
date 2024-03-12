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
"""Command for creating machine images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import kms_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope
from googlecloudsdk.command_lib.compute.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.compute.machine_images import flags as machine_image_flags


class Create(base.CreateCommand):
  """Create a Compute Engine machine image."""
  _ALLOW_RSA_ENCRYPTED_CSEK_KEYS = True

  detailed_help = {
      'brief':
          'Create a Compute Engine machine image.',
      'EXAMPLES':
          """
         To create a machine image, run:

           $ {command} my-machine-image --source-instance=example-source --source-instance-zone=us-central1-a
       """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(machine_image_flags.DEFAULT_LIST_FORMAT)
    Create.MACHINE_IMAGE_ARG = machine_image_flags.MakeMachineImageArg()
    Create.MACHINE_IMAGE_ARG.AddArgument(parser, operation_type='create')
    parser.add_argument(
        '--description',
        help='Specifies a text description of the machine image.')
    csek_utils.AddCsekKeyArgs(parser, resource_type='machine image')
    flags.AddStorageLocationFlag(parser, "machine image's")
    flags.AddGuestFlushFlag(parser, 'machine image')
    flags.AddSourceDiskCsekKeyArg(parser)
    kms_resource_args.AddKmsKeyResourceArg(parser, 'machine image')
    Create.SOURCE_INSTANCE = machine_image_flags.MakeSourceInstanceArg()
    Create.SOURCE_INSTANCE.AddArgument(parser)

  def Run(self, args):
    """Returns a list of requests necessary for adding machine images."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    machine_image_ref = Create.MACHINE_IMAGE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=scope.ScopeEnum.GLOBAL,
        scope_lister=flags.GetDefaultScopeLister(client))

    source_instance = Create.SOURCE_INSTANCE.ResolveAsResource(
        args, holder.resources)

    machine_image = client.messages.MachineImage(
        name=machine_image_ref.Name(),
        description=args.description,
        sourceInstance=source_instance.SelfLink())

    csek_keys = csek_utils.CsekKeyStore.FromArgs(
        args, self._ALLOW_RSA_ENCRYPTED_CSEK_KEYS)
    if csek_keys:
      machine_image.machineImageEncryptionKey = csek_utils.MaybeToMessage(
          csek_keys.LookupKey(
              machine_image_ref, raise_if_missing=args.require_csek_key_create),
          client.apitools_client)
    machine_image.machineImageEncryptionKey = kms_utils.MaybeGetKmsKey(
        args, client.messages, machine_image.machineImageEncryptionKey)

    if args.IsSpecified('storage_location'):
      machine_image.storageLocations = [args.storage_location]

    if args.IsSpecified('guest_flush'):
      machine_image.guestFlush = args.guest_flush

    source_csek_keys = getattr(args, 'source_disk_csek_key', [])

    disk_keys = {}

    if source_csek_keys:
      for key in source_csek_keys:
        disk_url = key.get('disk')
        disk_ref = holder.resources.Parse(
            disk_url,
            collection='compute.disks',
            params={
                'project': source_instance.project,
                'zone': source_instance.project
            })
        key_store = csek_utils.CsekKeyStore.FromFile(
            key.get('csek-key-file'), self._ALLOW_RSA_ENCRYPTED_CSEK_KEYS)

        disk_key = csek_utils.MaybeToMessage(
            key_store.LookupKey(disk_ref), client.apitools_client)
        disk_keys[disk_url] = disk_key

    source_disk_messages = []
    if disk_keys:
      for disk, key in disk_keys.items():
        source_disk_message = client.messages.SourceDiskEncryptionKey(
            sourceDisk=disk, diskEncryptionKey=key)
        source_disk_messages.append(source_disk_message)

    if source_disk_messages:
      machine_image.sourceDiskEncryptionKeys = source_disk_messages

    request = client.messages.ComputeMachineImagesInsertRequest(
        machineImage=machine_image, project=machine_image_ref.project)
    return client.MakeRequests([(client.apitools_client.machineImages, 'Insert',
                                 request)])
