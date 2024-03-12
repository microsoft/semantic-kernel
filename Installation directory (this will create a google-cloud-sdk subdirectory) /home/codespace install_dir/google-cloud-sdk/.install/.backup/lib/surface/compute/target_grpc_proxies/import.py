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
"""Import target command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_grpc_proxies import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


def _Describe(holder, target_grpc_proxy_ref):
  client = holder.client
  request = client.messages.ComputeTargetGrpcProxiesGetRequest(
      **target_grpc_proxy_ref.AsDict())
  collection = client.apitools_client.targetGrpcProxies
  return client.MakeRequests([(collection, 'Get', request)])[0]


def _Create(holder, target_grpc_proxy, target_grpc_proxy_ref):
  client = holder.client
  request = client.messages.ComputeTargetGrpcProxiesInsertRequest(
      project=target_grpc_proxy_ref.project, targetGrpcProxy=target_grpc_proxy)
  collection = client.apitools_client.targetGrpcProxies
  return client.MakeRequests([(collection, 'Insert', request)])[0]


def _Patch(client, target_grpc_proxy_ref, target_grpc_proxy):
  """Make target gRPC proxy patch request."""
  request = client.messages.ComputeTargetGrpcProxiesPatchRequest(
      project=target_grpc_proxy_ref.project,
      targetGrpcProxy=target_grpc_proxy_ref.Name(),
      targetGrpcProxyResource=target_grpc_proxy)
  collection = client.apitools_client.targetGrpcProxies
  return client.MakeRequests([(collection, 'Patch', request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import a target gRPC proxy."""

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
    cls.TARGET_GRPC_PROXY_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(parser, cls.GetSchemaPath(for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_grpc_proxy_ref = self.TARGET_GRPC_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

    try:
      target_grpc_proxy = export_util.Import(
          message_type=client.messages.TargetGrpcProxy,
          stream=data,
          schema_path=self.GetSchemaPath())
    except yaml_validator.ValidationError as e:
      raise compute_exceptions.ValidationError(str(e))

    # Get existing target gRPC proxy.
    try:
      target_grpc_proxy_old = _Describe(holder, target_grpc_proxy_ref)
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # Target gRPC proxy does not exit, create a new one.
      return _Create(holder, target_grpc_proxy, target_grpc_proxy_ref)

    if target_grpc_proxy_old == target_grpc_proxy:
      return

    console_io.PromptContinue(
        message=('Target Grpc Proxy [{0}] will be overwritten.').format(
            target_grpc_proxy_ref.Name()),
        cancel_on_no=True)

    # Populate id and fingerprint fields. These two fields are manually
    # removed from the schema files.
    target_grpc_proxy.id = target_grpc_proxy_old.id
    target_grpc_proxy.fingerprint = target_grpc_proxy_old.fingerprint

    return _Patch(client, target_grpc_proxy_ref, target_grpc_proxy)
