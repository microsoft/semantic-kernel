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
"""Command for removing project-wide metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class RemoveMetadata(base.UpdateCommand):
  """Remove project-wide metadata entries.

  *{command}* can be used to remove project-wide metadata entries.
  """

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--all',
        action='store_true',
        default=False,
        help='If provided, all metadata entries are removed.')
    group.add_argument(
        '--keys',
        type=arg_parsers.ArgList(min_length=1),
        metavar='KEY',
        help='The keys of the entries to remove.')

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
    new_object.commonInstanceMetadata = metadata_utils.RemoveEntries(
        client.messages,
        existing_metadata=existing_metadata,
        keys=args.keys,
        remove_all=args.all)

    if metadata_utils.MetadataEqual(existing_metadata,
                                    new_object.commonInstanceMetadata):
      return None
    else:
      return new_object

  def Run(self, args):
    if not args.all and not args.keys:
      raise exceptions.ArgumentError(
          'One of [--all] or [--keys] must be provided.')

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
