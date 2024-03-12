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
"""Command for updating target TCP proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.target_tcp_proxies import flags


class Update(base.SilentCommand):
  """Update a target TCP proxy."""

  BACKEND_SERVICE_ARG = None
  TARGET_TCP_PROXY_ARG = None

  @classmethod
  def Args(cls, parser):
    target_proxies_utils.AddProxyHeaderRelatedUpdateArgs(parser)

    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForTargetTcpProxy(
            required=False))
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.TARGET_TCP_PROXY_ARG = flags.TargetTcpProxyArgument()
    cls.TARGET_TCP_PROXY_ARG.AddArgument(parser, operation_type='update')

  def Run(self, args):
    if not (args.proxy_header or args.backend_service):
      raise exceptions.OneOfArgumentsRequiredException(
          ['--backend-service', '--proxy-header'],
          'You must specify at least one of [--backend-service] or '
          '[--proxy-header].')

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    requests = []
    target_tcp_proxy_ref = self.TARGET_TCP_PROXY_ARG.ResolveAsResource(
        args, holder.resources)

    client = holder.client.apitools_client
    messages = holder.client.messages

    if args.backend_service:
      backend_service_ref = self.BACKEND_SERVICE_ARG.ResolveAsResource(
          args, holder.resources)
      requests.append(
          (client.targetTcpProxies,
           'SetBackendService',
           messages.ComputeTargetTcpProxiesSetBackendServiceRequest(
               project=target_tcp_proxy_ref.project,
               targetTcpProxy=target_tcp_proxy_ref.Name(),
               targetTcpProxiesSetBackendServiceRequest=(
                   messages.TargetTcpProxiesSetBackendServiceRequest(
                       service=backend_service_ref.SelfLink())))))

    if args.proxy_header:
      proxy_header = (messages.TargetTcpProxiesSetProxyHeaderRequest.
                      ProxyHeaderValueValuesEnum(args.proxy_header))
      requests.append(
          (client.targetTcpProxies,
           'SetProxyHeader',
           messages.ComputeTargetTcpProxiesSetProxyHeaderRequest(
               project=target_tcp_proxy_ref.project,
               targetTcpProxy=target_tcp_proxy_ref.Name(),
               targetTcpProxiesSetProxyHeaderRequest=(
                   messages.TargetTcpProxiesSetProxyHeaderRequest(
                       proxyHeader=proxy_header)))))

    errors = []
    resources = holder.client.MakeRequests(requests, errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources


Update.detailed_help = {
    'brief': 'Update a target TCP proxy',
    'DESCRIPTION': """\

        *{command}* is used to change the backend service or proxy header
        of existing target TCP proxies. A target TCP proxy is referenced
        by one or more forwarding rules which define which packets the
        proxy is responsible for routing. The target TCP proxy in turn
        points to a backend service which will handle the requests.  """,
}
