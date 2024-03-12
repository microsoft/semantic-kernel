# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for adding metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
          {command} can be used to add or update the metadata of a
        virtual machine instance. Every instance has access to a
        metadata server that can be used to query metadata that has
        been set through this tool. For information on metadata, see
        [](https://cloud.google.com/compute/docs/metadata)

        Only metadata keys that are provided are mutated. Existing
        metadata entries will remain unaffected.

        In order to retrieve custom metadata, run:

            $ gcloud compute instances describe example-instance --zone
            us-central1-a --format="value(metadata)"

        where example-instance is the name of the virtual machine instance
        you're querying custom metadata from. For more information about
        querying custom instance or project metadata through the Cloud Platform
        Console or the API, see
        [](https://cloud.google.com/compute/docs/storing-retrieving-metadata#querying_custom_metadata).


        If you are using this command to manage SSH keys for your project, please note
        the [risks](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys#risks)
        of manual SSH key management as well as the required format for SSH key
        metadata, available at [](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys).
        """,
    'EXAMPLES':
        """\
        To add metadata under key ``{0}'' to an instance
        named ``{1}'', run:

          $ {2} {1} --metadata={0}="{3}"

        To add multiple key-value pairs at once, separate them with commas:

          $ {2} {1} --metadata={0}="{3}",unimportant-data=zero

        """.format('important-data', 'test-instance', '{command}',
                   '2 plus 2 equals 4')
}


class InstancesAddMetadata(base.UpdateCommand):
  """Add or update instance metadata."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='set metadata on')
    metadata_utils.AddMetadataArgs(parser, required=True)

  def CreateReference(self, client, resources, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args, resources, scope_lister=flags.GetInstanceZoneScopeLister(client))

  def GetGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances,
            'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def GetSetRequest(self, client, instance_ref, replacement):
    return (client.apitools_client.instances,
            'SetMetadata',
            client.messages.ComputeInstancesSetMetadataRequest(
                metadata=replacement.metadata,
                **instance_ref.AsDict()))

  def Modify(self, client, args, existing):
    new_object = encoding.CopyProtoMessage(existing)
    existing_metadata = existing.metadata
    new_object.metadata = metadata_utils.ConstructMetadataMessage(
        client.messages,
        metadata=args.metadata,
        metadata_from_file=args.metadata_from_file,
        existing_metadata=existing_metadata)

    if metadata_utils.MetadataEqual(existing_metadata, new_object.metadata):
      return None
    else:
      return new_object

  def Run(self, args):
    if not args.metadata and not args.metadata_from_file:
      raise calliope_exceptions.OneOfArgumentsRequiredException(
          ['--metadata', '--metadata-from-file'],
          'At least one of [--metadata] or [--metadata-from-file] must be '
          'provided.')

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    project_ref = self.CreateReference(client, holder.resources, args)
    get_request = self.GetGetRequest(client, project_ref)

    objects = client.MakeRequests([get_request])

    new_object = self.Modify(client, args, objects[0])

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if not new_object or objects[0] == new_object:
      log.status.Print(
          'No change requested; skipping update for [{0}].'.format(
              objects[0].name))
      return objects

    return client.MakeRequests(
        [self.GetSetRequest(client, project_ref, new_object)])


InstancesAddMetadata.detailed_help = DETAILED_HELP
