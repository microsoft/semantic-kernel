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
"""Command for creating target HTTP proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_http_proxies import flags
from googlecloudsdk.command_lib.compute.target_http_proxies import target_http_proxies_utils
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags


def _DetailedHelp():
  return {
      'brief': 'Create a target HTTP proxy.',
      'DESCRIPTION': """\
      *{command}* is used to create target HTTP proxies. A target
      HTTP proxy is referenced by one or more forwarding rules which
      specify the network traffic that the proxy is responsible for
      routing. The target HTTP proxy points to a URL map that defines
      the rules for routing the requests. The URL map's job is to map
      URLs to backend services which handle the actual requests.
      """,
      'EXAMPLES': """\
      If there is an already-created URL map with the name URL_MAP, create a
      global target HTTP proxy pointing to this map by running:

        $ {command} PROXY_NAME --url-map=URL_MAP

      Create a regional target HTTP proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --region=REGION_NAME

      To create a proxy with a textual description, run:

        $ {command} PROXY_NAME --url-map=URL_MAP --description="default proxy"
      """,
  }


def _Args(parser, traffic_director_security):
  """Add the target http proxies comamnd line flags to the parser."""
  parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
  parser.add_argument(
      '--description',
      help='An optional, textual description for the target HTTP proxy.',
  )
  parser.display_info.AddCacheUpdater(flags.TargetHttpProxiesCompleter)
  if traffic_director_security:
    flags.AddProxyBind(parser, False)

  target_proxies_utils.AddHttpKeepAliveTimeoutSec(parser)


def _Run(
    args, holder, url_map_ref, target_http_proxy_ref, traffic_director_security
):
  """Issue a Target HTTP Proxy Insert request."""
  client = holder.client

  if traffic_director_security and args.proxy_bind:
    target_http_proxy = client.messages.TargetHttpProxy(
        description=args.description,
        name=target_http_proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
        proxyBind=args.proxy_bind,
    )
  else:
    target_http_proxy = client.messages.TargetHttpProxy(
        description=args.description,
        name=target_http_proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
    )

  if args.IsSpecified('http_keep_alive_timeout_sec'):
    target_http_proxy.httpKeepAliveTimeoutSec = args.http_keep_alive_timeout_sec

  if target_http_proxies_utils.IsRegionalTargetHttpProxiesRef(
      target_http_proxy_ref
  ):
    request = client.messages.ComputeRegionTargetHttpProxiesInsertRequest(
        project=target_http_proxy_ref.project,
        region=target_http_proxy_ref.region,
        targetHttpProxy=target_http_proxy,
    )
    collection = client.apitools_client.regionTargetHttpProxies
  else:
    request = client.messages.ComputeTargetHttpProxiesInsertRequest(
        project=target_http_proxy_ref.project, targetHttpProxy=target_http_proxy
    )
    collection = client.apitools_client.targetHttpProxies

  return client.MakeRequests([(collection, 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a target HTTP proxy."""

  _traffic_director_security = False

  URL_MAP_ARG = None
  TARGET_HTTP_PROXY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTP_PROXY_ARG = flags.TargetHttpProxyArgument()
    cls.TARGET_HTTP_PROXY_ARG.AddArgument(parser, operation_type='create')
    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy()
    cls.URL_MAP_ARG.AddArgument(parser)
    _Args(parser, cls._traffic_director_security)

  def Run(self, args):
    """Issue a Target HTTP Proxy Insert request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    target_http_proxy_ref = self.TARGET_HTTP_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL
    )
    url_map_ref = target_http_proxies_utils.ResolveTargetHttpProxyUrlMap(
        args, self.URL_MAP_ARG, target_http_proxy_ref, holder.resources
    )
    return _Run(
        args,
        holder,
        url_map_ref,
        target_http_proxy_ref,
        self._traffic_director_security,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  _traffic_director_security = True
