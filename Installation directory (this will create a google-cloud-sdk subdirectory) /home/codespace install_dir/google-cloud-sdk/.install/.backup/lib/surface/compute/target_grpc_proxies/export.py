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
"""Export ssl policies command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_grpc_proxies import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


def _Describe(holder, target_grpc_proxy_ref):
  client = holder.client
  request = client.messages.ComputeTargetGrpcProxiesGetRequest(
      **target_grpc_proxy_ref.AsDict())
  collection = client.apitools_client.targetGrpcProxies

  return client.MakeRequests([(collection, 'Get', request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Export a target gRPC proxy."""

  TARGET_GRPC_PROXY_ARG = None

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'TargetGrpcProxy', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    cls.TARGET_GRPC_PROXY_ARG = flags.TargetGrpcProxyArgument()
    cls.TARGET_GRPC_PROXY_ARG.AddArgument(parser, operation_type='export')
    export_util.AddExportFlags(parser, cls.GetSchemaPath(for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    target_grpc_proxy_ref = self.TARGET_GRPC_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    target_grpc_proxy = _Describe(holder, target_grpc_proxy_ref)

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(
            message=target_grpc_proxy,
            stream=stream,
            schema_path=self.GetSchemaPath())

    else:
      export_util.Export(
          message=target_grpc_proxy,
          stream=sys.stdout,
          schema_path=self.GetSchemaPath())
