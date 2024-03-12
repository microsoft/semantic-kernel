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
"""Flags and helpers for the compute target-grpc-proxies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      urlMap.basename(),
      validateForProxyless
    )"""


class TargetGrpcProxiesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TargetGrpcProxiesCompleter, self).__init__(
        collection='compute.targetGrpcProxies',
        list_command='compute target-grpc-proxies list --uri',
        **kwargs)


def AddDescription(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the target gRPC proxy.')


def AddValidateForProxyless(parser):
  """Adds the validate_for_proxyless argument."""
  parser.add_argument(
      '--validate-for-proxyless',
      action='store_true',
      default=False,
      help="""\
      If specified, configuration in the associated urlMap and the
      BackendServices is checked to allow only the features that are supported
      in the latest release of gRPC.

      If unspecified, no such configuration checks are performed. This may cause
      unexpected behavior in gRPC applications if unsupported features are
      configured.
      """)


def TargetGrpcProxyArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='target gRPC proxy',
      completer=TargetGrpcProxiesCompleter,
      plural=plural,
      custom_plural='target gRPC proxies',
      required=required,
      global_collection='compute.targetGrpcProxies')
