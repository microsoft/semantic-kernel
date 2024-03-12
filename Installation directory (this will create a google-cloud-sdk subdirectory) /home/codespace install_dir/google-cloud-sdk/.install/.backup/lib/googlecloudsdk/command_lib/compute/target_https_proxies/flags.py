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
"""Flags and helpers for the compute target-https-proxies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util import completers

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      sslCertificates.map().basename().list():label=SSL_CERTIFICATES,
      urlMap.basename(),
      region.basename(),
      certificateMap.basename()
    )"""


class GlobalTargetHttpsProxiesCompleter(compute_completers.ListCommandCompleter
                                       ):

  def __init__(self, **kwargs):
    super(GlobalTargetHttpsProxiesCompleter, self).__init__(
        collection='compute.targetHttpsProxies',
        list_command='compute target-https-proxies list --global --uri',
        **kwargs)


class RegionTargetHttpsProxiesCompleter(compute_completers.ListCommandCompleter
                                       ):

  def __init__(self, **kwargs):
    super(RegionTargetHttpsProxiesCompleter, self).__init__(
        collection='compute.regionTargetHttpsProxies',
        list_command='compute target-https-proxies list --filter=region:* --uri',
        **kwargs)


class TargetHttpsProxiesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(TargetHttpsProxiesCompleter, self).__init__(
        completers=[
            GlobalTargetHttpsProxiesCompleter, RegionTargetHttpsProxiesCompleter
        ],
        **kwargs)


def AddProxyBind(parser, default):
  """Adds the proxy bind argument."""
  parser.add_argument(
      '--proxy-bind',
      action='store_true',
      default=default,
      help="""\
      This flag applies when the load_balancing_scheme of the associated
      backend service is INTERNAL_SELF_MANAGED. When specified, the envoy binds
      to the forwarding rule's IP address and port. By default, this flag is
      off.
      """)


def TargetHttpsProxyArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='target HTTPS proxy',
      completer=TargetHttpsProxiesCompleter,
      plural=plural,
      custom_plural='target HTTPS proxies',
      required=required,
      global_collection='compute.targetHttpsProxies',
      regional_collection='compute.regionTargetHttpsProxies',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)
