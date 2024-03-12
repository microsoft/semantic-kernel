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
"""Command for describing routes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routes import flags


class Describe(base.DescribeCommand):
  r"""Describe a route.

  *{command}* displays all data associated with a Compute
  Engine route in a project.

  ## EXAMPLES

  To describe a route with the name 'route-name', run:

    $ {command} route-name

  """

  ROUTE_ARG = None

  @staticmethod
  def Args(parser):
    Describe.ROUTE_ARG = flags.RouteArgument()
    Describe.ROUTE_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    route_ref = self.ROUTE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeRoutesGetRequest(
        **route_ref.AsDict())

    return client.MakeRequests([(client.apitools_client.routes,
                                 'Get', request)])[0]
