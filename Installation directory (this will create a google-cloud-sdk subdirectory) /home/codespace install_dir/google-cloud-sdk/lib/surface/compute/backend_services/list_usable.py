# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for listing backend services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    "DESCRIPTION": """\
        *{command}* retrieves the list of backend service resources in the
        specified project for which you have compute.backendService.get
        and compute.backendService.use permissions. This command is useful
        when you're creating load balancers in a Shared VPC environment
        and you want to use [cross-project service
        referencing](https://cloud.google.com/load-balancing/docs/https#cross-project).
        You can use this command to find out which backend
        services in other projects are available to you for referencing.
        """,
    "EXAMPLES": """\
        To list all global backend services in a project, run:

          $ {command} --global

        To list all backend services in a region, run:

          $ {command} --region=REGION
        """,
}


class ListUsable(base.ListCommand):
  """List usable backend services."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_NOT_REQUIRED_ARG.AddArgument(parser)
    parser.display_info.AddFormat(flags.DEFAULT_BETA_LIST_FORMAT)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    resource_scope, scope_value = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_NOT_REQUIRED_ARG.scopes.SpecifiedByArgs(
            args
        )
    )

    if resource_scope.scope_enum == compute_scope.ScopeEnum.GLOBAL:
      request = messages.ComputeBackendServicesListUsableRequest(
          project=properties.VALUES.core.project.Get(required=True)
      )
      apitools = client.apitools_client.backendServices
    elif resource_scope.scope_enum == compute_scope.ScopeEnum.REGION:
      request = messages.ComputeRegionBackendServicesListUsableRequest(
          region=scope_value,
          project=properties.VALUES.core.project.Get(required=True),
      )
      apitools = client.apitools_client.regionBackendServices

    return list_pager.YieldFromList(
        apitools,
        request,
        method="ListUsable",
        batch_size_attribute="maxResults",
        batch_size=500,
        field="items",
    )
