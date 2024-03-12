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
"""Command for adding project-wide metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class AddMetadata(base.UpdateCommand):
  # pylint:disable=line-too-long
  """Add or update project-wide metadata.

    *{command}* can be used to add or update project-wide
  metadata. Every instance has access to a metadata server that
  can be used to query metadata that has been set through this
  tool. Project-wide metadata entries are visible to all
  instances. To set metadata for individual instances, use
  `gcloud compute instances add-metadata`. For information on
  metadata, see
  [](https://cloud.google.com/compute/docs/metadata)

  Only metadata keys that are provided are mutated. Existing
  metadata entries will remain unaffected.

  If you are using this command to manage SSH keys for your project, please note
  the
  [risks](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys#risks)
  of manual SSH key management as well as the required format for SSH key
  metadata, available at
  [](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys)
  """
  # pylint:enable=line-too-long

  @staticmethod
  def Args(parser):
    metadata_utils.AddMetadataArgs(parser, required=True)

  def CreateReference(self, resources):
    return resources.Parse(
        properties.VALUES.core.project.GetOrFail(),
        collection='compute.projects')

  def GetGetRequest(self, client, project_ref):
    return (client.apitools_client.projects,
            'Get',
            client.messages.ComputeProjectsGetRequest(**project_ref.AsDict()))

  def GetSetRequest(self, client, project_ref, replacement):
    return (client.apitools_client.projects,
            'SetCommonInstanceMetadata',
            client.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
                metadata=replacement.commonInstanceMetadata,
                **project_ref.AsDict()))

  def Modify(self, client, args, existing):
    new_object = encoding.JsonToMessage(
        type(existing), encoding.MessageToJson(existing))
    existing_metadata = existing.commonInstanceMetadata
    new_object.commonInstanceMetadata = metadata_utils.ConstructMetadataMessage(
        client.messages,
        metadata=args.metadata,
        metadata_from_file=args.metadata_from_file,
        existing_metadata=existing_metadata)

    if metadata_utils.MetadataEqual(existing_metadata,
                                    new_object.commonInstanceMetadata):
      return None
    else:
      return new_object

  def Run(self, args):
    if not args.metadata and not args.metadata_from_file:
      raise compute_exceptions.ArgumentError(
          'At least one of [--metadata] or [--metadata-from-file] must be '
          'provided.')

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    project_ref = self.CreateReference(holder.resources)
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
