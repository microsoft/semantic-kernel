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
"""Command for deleting target gRPC proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_grpc_proxies import flags


def _DetailedHelp():
  return {
      'brief':
          'Delete one or more target gRPC proxy.',
      'DESCRIPTION':
          """\
      *{command}* deletes one or more target gRPC proxies.
      """,
      'EXAMPLES':
          """\
      Delete a global target gRPC proxy by running:

        $ {command} PROXY_NAME
      """,
  }


def _Run(holder, target_grpc_proxy_refs):
  """Issues requests necessary to delete Target gRPC Proxies."""
  client = holder.client
  utils.PromptForDeletion(target_grpc_proxy_refs)

  requests = []
  for target_grpc_proxy_ref in target_grpc_proxy_refs:
    requests.append((client.apitools_client.targetGrpcProxies, 'Delete',
                     client.messages.ComputeTargetGrpcProxiesDeleteRequest(
                         **target_grpc_proxy_ref.AsDict())))

  return client.MakeRequests(requests)


class Delete(base.DeleteCommand):
  """Delete one or more target gRPC proxies."""

  TARGET_GRPC_PROXY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_GRPC_PROXY_ARG = flags.TargetGrpcProxyArgument(plural=True)
    cls.TARGET_GRPC_PROXY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.TargetGrpcProxiesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    target_grpc_proxy_refs = self.TARGET_GRPC_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    return _Run(holder, target_grpc_proxy_refs)
