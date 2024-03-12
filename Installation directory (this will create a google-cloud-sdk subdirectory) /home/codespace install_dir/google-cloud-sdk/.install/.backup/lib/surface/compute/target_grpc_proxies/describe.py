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
"""Command for describing target gRPC proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_grpc_proxies import flags


def _DetailedHelp():
  return {
      'brief':
          'Display detailed information about a target gRPC proxy.',
      'DESCRIPTION':
          """\
        *{command}* displays all data associated with a Compute Engine
        target gRPC proxy.
      """,
      'EXAMPLES':
          """\
      To describe a global target gRPC proxy, run:

        $ {command} PROXY_NAME
      """,
  }


def _Run(holder, target_grpc_proxy_ref):
  """Issues requests necessary to describe Target gRPC Proxies."""
  client = holder.client
  request = client.messages.ComputeTargetGrpcProxiesGetRequest(
      **target_grpc_proxy_ref.AsDict())
  collection = client.apitools_client.targetGrpcProxies

  return client.MakeRequests([(collection, 'Get', request)])[0]


class Describe(base.DescribeCommand):
  """Display detailed information about a target gRPC proxy."""

  TARGET_GRPC_PROXY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_GRPC_PROXY_ARG = flags.TargetGrpcProxyArgument()
    cls.TARGET_GRPC_PROXY_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    target_grpc_proxy_ref = self.TARGET_GRPC_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    return _Run(holder, target_grpc_proxy_ref)
