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
"""Command for deleting routes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routes import flags


class Delete(base.DeleteCommand):
  r"""Delete routes.

  *{command}* deletes one or more Compute Engine routes.

  ## EXAMPLES

  To delete a route with the name 'route-name', run:

    $ {command} route-name

  To delete two routes with the names 'route-name1' and 'route-name2',
  run:

    $ {command} route-name1 route-name2

  """

  ROUTE_ARG = None

  @staticmethod
  def Args(parser):
    Delete.ROUTE_ARG = flags.RouteArgument(plural=True)
    Delete.ROUTE_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(completers.RoutesCompleter)

  def Run(self, args):
    """Issues requests necessary to delete Routes."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    route_refs = Delete.ROUTE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(route_refs)

    requests = []
    for route_ref in route_refs:
      requests.append((client.apitools_client.routes, 'Delete',
                       client.messages.ComputeRoutesDeleteRequest(
                           **route_ref.AsDict())))

    return client.MakeRequests(requests)
