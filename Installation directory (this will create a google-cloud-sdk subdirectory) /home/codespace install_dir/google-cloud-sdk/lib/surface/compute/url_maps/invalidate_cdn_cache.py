# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for cache invalidation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils
from googlecloudsdk.core import log


def _DetailedHelp():
  return {
      'brief':
          'Invalidate specified objects for a URL map in Cloud CDN caches.',
      'DESCRIPTION':
          """\
      *{command}* requests that Cloud CDN stop using cached content for
      resources at a particular URL path or set of URL paths.

      *{command}* may succeed even if no content is cached for some or all
      URLs with the given path.
      """,
  }


def _Args(parser):
  """Add invalidate-cdn-cache arguments to the parser."""

  parser.add_argument(
      '--path',
      required=True,
      help="""\
      A path specifying which objects to invalidate. PATH must start with
      ``/'' and the only place a ``*'' is allowed is at the end following a
      ``/''. It will be matched against URL paths, which do not include
      scheme, host, or any text after the first ``?'' or ``#'' (and those
      characters are not allowed here). For example, for the URL
      ``https://example.com/whatever/x.html?a=b'', the path is
      ``/whatever/x.html''.

      If PATH ends with ``*'', the preceding string is a prefix, and all URLs
      whose paths begin with it will be invalidated. If PATH doesn't end with
      ``*'', then only URLs with exactly that path will be invalidated.

      Examples:
      - ``'', ``*'', anything that doesn't start with ``/'': error
      - ``/'': just the root URL
      - ``/*'': everything
      - ``/x/y'': ``/x/y'' only (and not ``/x/y/'')
      - ``/x/y/'': ``/x/y/'' only (and not ``/x/y'')
      - ``/x/y/*'': ``/x/y/'' and everything under it
      """)

  parser.add_argument(
      '--host',
      required=False,
      default=None,
      help="""\
      If set, this invalidation will apply only to requests to the
      specified host.
      """)

  base.ASYNC_FLAG.AddToParser(parser)


def _CreateRequests(holder, args, url_map_arg):
  """Returns a list of requests necessary for cache invalidations."""
  url_map_ref = url_map_arg.ResolveAsResource(
      args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  cache_invalidation_rule = holder.client.messages.CacheInvalidationRule(
      path=args.path)
  if args.host is not None:
    cache_invalidation_rule.host = args.host

  messages = holder.client.messages
  if url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
    request = messages.ComputeRegionUrlMapsInvalidateCacheRequest(
        project=url_map_ref.project,
        urlMap=url_map_ref.Name(),
        cacheInvalidationRule=cache_invalidation_rule,
        region=url_map_ref.region)
    collection = holder.client.apitools_client.regionUrlMaps
  else:
    request = messages.ComputeUrlMapsInvalidateCacheRequest(
        project=url_map_ref.project,
        urlMap=url_map_ref.Name(),
        cacheInvalidationRule=cache_invalidation_rule)
    collection = holder.client.apitools_client.urlMaps

  return [(collection, 'InvalidateCache', request)]


def _Run(args, holder, url_map_arg):
  """Issues requests necessary to invalidate a URL map cdn cache."""
  client = holder.client

  requests = _CreateRequests(holder, args, url_map_arg)
  if args.async_:
    resources, errors = batch_helper.MakeRequests(
        requests=requests,
        http=client.apitools_client.http,
        batch_url=client.batch_url)
    if not errors:
      for invalidation_operation in resources:
        log.status.write('Invalidation pending for [{0}]\n'.format(
            invalidation_operation.targetLink))
        log.status.write('Monitor its progress at [{0}]\n'.format(
            invalidation_operation.selfLink))
    else:
      utils.RaiseToolException(errors)
  else:
    # We want to run through the generator that MakeRequests returns in order
    # to actually make the requests.
    resources = client.MakeRequests(requests)

  return resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class InvalidateCdnCache(base.SilentCommand):
  """Invalidate specified objects for a URL map in Cloud CDN caches."""

  detailed_help = _DetailedHelp()
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser, cust_metavar='URLMAP')
    _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.URL_MAP_ARG)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class InvalidateCdnCacheBeta(InvalidateCdnCache):
  pass


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InvalidateCdnCacheAlpha(InvalidateCdnCacheBeta):
  pass
