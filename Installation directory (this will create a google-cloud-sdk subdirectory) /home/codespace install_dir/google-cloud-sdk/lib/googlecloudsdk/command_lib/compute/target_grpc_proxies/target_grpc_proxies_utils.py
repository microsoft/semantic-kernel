# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple target-grpc-proxies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import scope as compute_scope


def ResolveTargetGrpcProxyUrlMap(args, url_map_arg, target_grpc_proxy_ref,
                                 resources):
  """Parses the URL map that is pointed to by a target gRPC proxy from args.

  This function handles parsing a regional/global URL map that is
  pointed to by a regional/global target gRPC proxy.

  Args:
    args: The arguments provided to the target_grpc_proxies command.
    url_map_arg: The ResourceArgument specification for the url map argument.
    target_grpc_proxy_ref: The resource reference to the target gRPC proxy. This
      is obtained by parsing the target gRPC proxy arguments provided.
    resources: ComputeApiHolder resources.

  Returns:
    Returns the URL map resource
  """
  if not compute_scope.IsSpecifiedForFlag(args, 'url_map'):
    if IsRegionalTargetGrpcProxiesRef(target_grpc_proxy_ref):
      args.url_map_region = target_grpc_proxy_ref.region
    else:
      args.global_url_map = args.url_map

  return url_map_arg.ResolveAsResource(args, resources)


def IsRegionalTargetGrpcProxiesRef(target_grpc_proxy_ref):
  """Returns True if the target gRPC proxy reference is regional."""
  return target_grpc_proxy_ref.Collection() == 'compute.regionTargetGrpcProxies'


def IsGlobalTargetGrpcProxiesRef(target_grpc_proxy_ref):
  """Returns True if the target gRPC proxy reference is global."""
  return target_grpc_proxy_ref.Collection() == 'compute.targetGrpcProxies'
