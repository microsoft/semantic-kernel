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
"""Command for describing target HTTP proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_http_proxies import flags
from googlecloudsdk.command_lib.compute.target_http_proxies import target_http_proxies_utils


def _DetailedHelp():
  return {
      'brief':
          'Display detailed information about a target HTTP proxy.',
      'DESCRIPTION':
          """\
        *{command}* displays all data associated with a target HTTP proxy
        in a project.
      """,
      'EXAMPLES':
          """\
      To describe a global target HTTP proxy, run:

        $ {command} PROXY_NAME

      To describe a regional target HTTP proxy, run:

        $ {command} PROXY_NAME --region=REGION_NAME
      """,
  }


def _Run(holder, target_http_proxy_ref):
  """Issues requests necessary to describe Target HTTP Proxies."""
  client = holder.client
  if target_http_proxies_utils.IsRegionalTargetHttpProxiesRef(
      target_http_proxy_ref):
    request = client.messages.ComputeRegionTargetHttpProxiesGetRequest(
        **target_http_proxy_ref.AsDict())
    collection = client.apitools_client.regionTargetHttpProxies
  else:
    request = client.messages.ComputeTargetHttpProxiesGetRequest(
        **target_http_proxy_ref.AsDict())
    collection = client.apitools_client.targetHttpProxies

  return client.MakeRequests([(collection, 'Get', request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Display detailed information about a target HTTP proxy."""

  TARGET_HTTP_PROXY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTP_PROXY_ARG = flags.TargetHttpProxyArgument()
    cls.TARGET_HTTP_PROXY_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    target_http_proxy_ref = self.TARGET_HTTP_PROXY_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    return _Run(holder, target_http_proxy_ref)
