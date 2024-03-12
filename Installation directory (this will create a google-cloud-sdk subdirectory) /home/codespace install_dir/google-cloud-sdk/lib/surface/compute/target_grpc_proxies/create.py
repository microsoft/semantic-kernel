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
"""Command for creating target gRPC proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_grpc_proxies import flags
from googlecloudsdk.command_lib.compute.target_grpc_proxies import target_grpc_proxies_utils
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags


def _DetailedHelp():
  return {
      'brief':
          'Create a target gRPC proxy.',
      'DESCRIPTION':
          """\
      *{command}* is used to create target gRPC proxies. A target gRPC proxy is
      a component of load balancers intended for load balancing gRPC traffic.
      Global forwarding rules reference a target gRPC proxy. The Target gRPC
      proxy references a URL map which specifies how traffic routes to gRPC
      backend services.
      """,
      'EXAMPLES':
          """\
      If there is an already-created URL map with the name URL_MAP, create a
      global target gRPC proxy pointing to this map by running:

        $ {command} PROXY_NAME --url-map=URL_MAP

      To create a proxy with a textual description, run:

        $ {command} PROXY_NAME --url-map=URL_MAP --description="default proxy"
      """,
  }


class Create(base.CreateCommand):
  """Create a target gRPC proxy."""

  URL_MAP_ARG = None
  TARGET_GRPC_PROXY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_GRPC_PROXY_ARG = flags.TargetGrpcProxyArgument()
    cls.TARGET_GRPC_PROXY_ARG.AddArgument(parser, operation_type='create')
    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        proxy_type='gRPC')
    cls.URL_MAP_ARG.AddArgument(parser)

    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    parser.display_info.AddCacheUpdater(flags.TargetGrpcProxiesCompleter)

    flags.AddDescription(parser)
    flags.AddValidateForProxyless(parser)

  def Run(self, args):
    """Issue a Target gRPC Proxy Insert request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    target_grpc_proxy_ref = self.TARGET_GRPC_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    url_map_ref = target_grpc_proxies_utils.ResolveTargetGrpcProxyUrlMap(
        args, self.URL_MAP_ARG, target_grpc_proxy_ref, holder.resources)

    client = holder.client
    target_grpc_proxy = client.messages.TargetGrpcProxy(
        description=args.description,
        name=target_grpc_proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
        validateForProxyless=args.validate_for_proxyless)
    request = client.messages.ComputeTargetGrpcProxiesInsertRequest(
        project=target_grpc_proxy_ref.project,
        targetGrpcProxy=target_grpc_proxy)
    collection = client.apitools_client.targetGrpcProxies
    return client.MakeRequests([(collection, 'Insert', request)])
