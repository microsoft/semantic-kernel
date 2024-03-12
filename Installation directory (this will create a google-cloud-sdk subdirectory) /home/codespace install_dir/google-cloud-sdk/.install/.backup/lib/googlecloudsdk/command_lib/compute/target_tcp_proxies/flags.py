# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute target-tcp-proxies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


class GlobalTargetTcpProxiesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalTargetTcpProxiesCompleter, self).__init__(
        collection='compute.targetTcpProxies',
        list_command='compute target-tcp-proxies list --global --uri',
        **kwargs)


class RegionalTargetTcpProxiesCompleter(compute_completers.ListCommandCompleter
                                       ):

  def __init__(self, **kwargs):
    super(RegionalTargetTcpProxiesCompleter, self).__init__(
        collection='compute.regionTargetTcpProxies',
        list_command='compute target-tcp-proxies list --filter=region:* --uri',
        **kwargs)


class TargetTcpProxiesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TargetTcpProxiesCompleter, self).__init__(
        completers=[
            GlobalTargetTcpProxiesCompleter, RegionalTargetTcpProxiesCompleter
        ],
        **kwargs)


class GATargetTcpProxiesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GATargetTcpProxiesCompleter, self).__init__(
        collection='compute.targetTcpProxies',
        list_command='compute target-tcp-proxies list --uri',
        **kwargs)


def TargetTcpProxyArgument(required=True, plural=False, allow_regional=False):
  return compute_flags.ResourceArgument(
      resource_name='target TCP proxy',
      completer=TargetTcpProxiesCompleter,
      plural=plural,
      custom_plural='target TCP proxies',
      required=required,
      global_collection='compute.targetTcpProxies',
      regional_collection='compute.regionTargetTcpProxies'
      if allow_regional else None,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def AddProxyBind(parser):
  """Adds the --proxy-bind argument."""
  parser.add_argument(
      '--proxy-bind',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      This field only applies when the forwarding rule that references this
      target proxy has a `--load-balancing-scheme` set to `INTERNAL_SELF_MANAGED`.

      When this field is set to `true`, Envoy proxies set up inbound traffic
      interception and bind to the IP address and port specified in the
      forwarding rule. This is generally useful when using Traffic Director to
      configure Envoy as a gateway or middle proxy (in other words, not a
      sidecar proxy). The Envoy proxy listens for inbound requests and handles
      requests when it receives them.
      """)
