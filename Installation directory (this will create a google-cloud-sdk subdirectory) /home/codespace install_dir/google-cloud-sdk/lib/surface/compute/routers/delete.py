# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for deleting Compute Engine routers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags


class Delete(base.DeleteCommand):
  """Delete Compute Engine routers.

  *{command}* deletes one or more Compute Engine
  routers. Routers can only be deleted when no other resources
  (e.g., virtual machine instances) refer to them.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    Delete.ROUTER_ARG = flags.RouterArgument(plural=True)
    Delete.ROUTER_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.RoutersCompleter)

  def Run(self, args):
    """Issues requests necessary to delete Routers."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_refs = Delete.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(router_refs, 'region')

    requests = []
    for router_ref in router_refs:
      requests.append((client.apitools_client.routers, 'Delete',
                       client.messages.ComputeRoutersDeleteRequest(
                           **router_ref.AsDict())))

    return client.MakeRequests(requests)
