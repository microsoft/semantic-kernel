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

"""Command for describing backend services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags


class Describe(base.DescribeCommand):
  """Describe a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(
        parser, operation_type='describe')

  def Run(self, args):
    """Issues request necessary to describe the backend service."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    (backend_services_utils.
     IsDefaultRegionalBackendServicePropertyNoneWarnOtherwise())
    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))

    if backend_service_ref.Collection() == 'compute.backendServices':
      service = client.apitools_client.backendServices
      request = client.messages.ComputeBackendServicesGetRequest(
          **backend_service_ref.AsDict())
    elif backend_service_ref.Collection() == 'compute.regionBackendServices':
      service = client.apitools_client.regionBackendServices
      request = client.messages.ComputeRegionBackendServicesGetRequest(
          **backend_service_ref.AsDict())

    return client.MakeRequests([(service, 'Get', request)])[0]


Describe.detailed_help = base_classes.GetMultiScopeDescriberHelp(
    'backend service', [base_classes.ScopeType.regional_scope,
                        base_classes.ScopeType.global_scope])
