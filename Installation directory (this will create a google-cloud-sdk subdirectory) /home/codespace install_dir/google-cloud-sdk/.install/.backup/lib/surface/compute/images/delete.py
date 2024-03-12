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
"""Command for deleting images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.images import flags


class Delete(base.DeleteCommand):
  """Delete Compute Engine images."""

  @staticmethod
  def Args(parser):
    Delete.DiskImageArg = flags.MakeDiskImageArg(plural=True)
    Delete.DiskImageArg.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.ImagesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    image_refs = Delete.DiskImageArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(image_refs)

    requests = []
    for image_ref in image_refs:
      requests.append((client.apitools_client.images, 'Delete',
                       client.messages.ComputeImagesDeleteRequest(
                           **image_ref.AsDict())))

    return client.MakeRequests(requests)


Delete.detailed_help = {
    'DESCRIPTION':
        '*{command}* deletes one or more Compute Engine images.',
    'EXAMPLES':
        """
        To delete images 'my-image1' and 'my-image2', run:

            $ {command} my-image1 my-image2
        """,
}
