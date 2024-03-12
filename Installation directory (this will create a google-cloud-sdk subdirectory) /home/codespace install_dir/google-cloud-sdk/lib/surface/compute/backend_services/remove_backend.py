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

"""Command for removing a backend from a backend service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class RemoveBackend(base.UpdateCommand):
  """Remove a backend from a backend service.

  *{command}* is used to remove a backend from a backend
  service.

  Before removing a backend, it is a good idea to "drain" the
  backend first. A backend can be drained by setting its
  capacity scaler to zero through 'gcloud compute
  backend-services edit'.
  """

  support_global_neg = True
  support_region_neg = True

  @classmethod
  def Args(cls, parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddInstanceGroupAndNetworkEndpointGroupArgs(
        parser,
        'remove from',
        support_global_neg=cls.support_global_neg,
        support_region_neg=cls.support_region_neg)

  def GetGetRequest(self, client, backend_service_ref):
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return (client.apitools_client.regionBackendServices,
              'Get',
              client.messages.ComputeRegionBackendServicesGetRequest(
                  backendService=backend_service_ref.Name(),
                  region=backend_service_ref.region,
                  project=backend_service_ref.project))
    return (client.apitools_client.backendServices,
            'Get',
            client.messages.ComputeBackendServicesGetRequest(
                backendService=backend_service_ref.Name(),
                project=backend_service_ref.project))

  def GetSetRequest(self, client, backend_service_ref, replacement):
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return (client.apitools_client.regionBackendServices,
              'Update',
              client.messages.ComputeRegionBackendServicesUpdateRequest(
                  backendService=backend_service_ref.Name(),
                  backendServiceResource=replacement,
                  region=backend_service_ref.region,
                  project=backend_service_ref.project))
    return (client.apitools_client.backendServices,
            'Update',
            client.messages.ComputeBackendServicesUpdateRequest(
                backendService=backend_service_ref.Name(),
                backendServiceResource=replacement,
                project=backend_service_ref.project))

  def _GetGroupRef(self, args, resources, client):
    if args.instance_group:
      return flags.MULTISCOPE_INSTANCE_GROUP_ARG.ResolveAsResource(
          args,
          resources,
          scope_lister=compute_flags.GetDefaultScopeLister(client))
    if args.network_endpoint_group:
      return flags.GetNetworkEndpointGroupArg(
          support_global_neg=self.support_global_neg,
          support_region_neg=self.support_region_neg).ResolveAsResource(
              args,
              resources,
              scope_lister=compute_flags.GetDefaultScopeLister(client))

  def Modify(self, client, resources, backend_service_ref, args, existing):
    replacement = encoding.CopyProtoMessage(existing)

    group_ref = self._GetGroupRef(args, resources, client)
    group_uri = group_ref.RelativeName()

    backend_idx = None
    for i, backend in enumerate(existing.backends):
      if group_uri == resources.ParseURL(backend.group).RelativeName():
        backend_idx = i

    if backend_idx is None:
      scope_value = getattr(group_ref, 'region', None)
      if scope_value is None:
        scope_value = getattr(group_ref, 'zone', None)
        scope = 'zone'
      else:
        scope = 'region'

      raise exceptions.ArgumentError(
          'Backend [{0}] in {1} [{2}] is not a backend of backend service '
          '[{3}].'.format(group_ref.Name(),
                          scope,
                          scope_value,
                          backend_service_ref.Name()))
    else:
      replacement.backends.pop(backend_idx)

    return replacement

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))
    get_request = self.GetGetRequest(client, backend_service_ref)

    objects = client.MakeRequests([get_request])

    new_object = self.Modify(client, holder.resources, backend_service_ref,
                             args, objects[0])

    return client.MakeRequests(
        [self.GetSetRequest(client, backend_service_ref, new_object)])
