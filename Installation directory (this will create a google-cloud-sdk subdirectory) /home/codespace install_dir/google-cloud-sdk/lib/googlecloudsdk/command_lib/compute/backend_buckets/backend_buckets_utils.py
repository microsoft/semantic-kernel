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
"""Code that's shared between multiple backend-buckets subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding


def GetNegativeCachingPolicy(client, args, backend_bucket):
  """Returns the negative caching policy.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_bucket: The backend bucket object. If the backend bucket object
      contains a negative caching policy already, it is used as the base to
      apply changes based on args.

  Returns:
    The negative caching policy.
  """
  negative_caching_policy = None
  if args.negative_caching_policy:
    negative_caching_policy = []
    for code, ttl in args.negative_caching_policy.items():
      negative_caching_policy.append(
          client.messages.BackendBucketCdnPolicyNegativeCachingPolicy(
              code=code, ttl=ttl))
  else:
    if (backend_bucket.cdnPolicy is not None and
        backend_bucket.cdnPolicy.negativeCachingPolicy is not None):
      negative_caching_policy = backend_bucket.cdnPolicy.negativeCachingPolicy

  return negative_caching_policy


def GetBypassCacheOnRequestHeaders(client, args):
  """Returns bypass cache on request headers.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.

  Returns:
    The bypass cache on request headers.
  """
  bypass_cache_on_request_headers = None
  if args.bypass_cache_on_request_headers:
    bypass_cache_on_request_headers = []
    for header in args.bypass_cache_on_request_headers:
      bypass_cache_on_request_headers.append(
          client.messages.BackendBucketCdnPolicyBypassCacheOnRequestHeader(
              headerName=header))

  return bypass_cache_on_request_headers


def HasCacheKeyPolicyArgs(args):
  """Returns true if the request requires a CacheKeyPolicy message.

  Args:
    args: The arguments passed to the gcloud command.

  Returns:
    True if there are cache key policy related arguments which require adding
    a CacheKeyPolicy message in the request.
  """
  return (args.IsSpecified('cache_key_query_string_whitelist') or
          args.IsSpecified('cache_key_include_http_header'))


def GetCacheKeyPolicy(client, args, backend_bucket):
  """Returns the cache key policy.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_bucket: The backend bucket object. If the backend bucket object
      contains a cache key policy already, it is used as the base to apply
      changes based on args.

  Returns:
    The cache key policy.
  """
  cache_key_policy = client.messages.BackendBucketCdnPolicyCacheKeyPolicy()
  if (backend_bucket.cdnPolicy is not None and
      backend_bucket.cdnPolicy.cacheKeyPolicy is not None):
    cache_key_policy = backend_bucket.cdnPolicy.cacheKeyPolicy

  if args.cache_key_include_http_header is not None:
    cache_key_policy.includeHttpHeaders = args.cache_key_include_http_header
  if args.cache_key_query_string_whitelist is not None:
    cache_key_policy.queryStringWhitelist = (
        args.cache_key_query_string_whitelist)

  return cache_key_policy


def ApplyCdnPolicyArgs(client,
                       args,
                       backend_bucket,
                       is_update=False,
                       cleared_fields=None):
  """Applies the CdnPolicy arguments to the specified backend bucket.

  If there are no arguments related to CdnPolicy, the backend bucket remains
  unmodified.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_bucket: The backend bucket object.
    is_update: True if this is called on behalf of an update command instead of
      a create command, False otherwise.
    cleared_fields: Reference to list with fields that should be cleared. Valid
      only for update command.
  """
  if backend_bucket.cdnPolicy is not None:
    cdn_policy = encoding.CopyProtoMessage(backend_bucket.cdnPolicy)
  else:
    cdn_policy = client.messages.BackendBucketCdnPolicy()

  if args.IsSpecified('signed_url_cache_max_age'):
    cdn_policy.signedUrlCacheMaxAgeSec = args.signed_url_cache_max_age

  if args.request_coalescing is not None:
    cdn_policy.requestCoalescing = args.request_coalescing

  if args.cache_mode:
    cdn_policy.cacheMode = client.messages.BackendBucketCdnPolicy.\
      CacheModeValueValuesEnum(args.cache_mode)
  if args.client_ttl is not None:
    cdn_policy.clientTtl = args.client_ttl
  if args.default_ttl is not None:
    cdn_policy.defaultTtl = args.default_ttl
  if args.max_ttl is not None:
    cdn_policy.maxTtl = args.max_ttl

  if is_update:
    # Takes care of resetting fields that are invalid for given cache modes
    should_clean_client_ttl = (
        args.cache_mode == 'USE_ORIGIN_HEADERS' and args.client_ttl is None)
    if args.no_client_ttl or should_clean_client_ttl:
      cleared_fields.append('cdnPolicy.clientTtl')
      cdn_policy.clientTtl = None

    should_clean_default_ttl = (
        args.cache_mode == 'USE_ORIGIN_HEADERS' and args.default_ttl is None)
    if args.no_default_ttl or should_clean_default_ttl:
      cleared_fields.append('cdnPolicy.defaultTtl')
      cdn_policy.defaultTtl = None

    should_clean_max_ttl = (args.cache_mode == 'USE_ORIGIN_HEADERS' or
                            args.cache_mode
                            == 'FORCE_CACHE_ALL') and args.max_ttl is None
    if args.no_max_ttl or should_clean_max_ttl:
      cleared_fields.append('cdnPolicy.maxTtl')
      cdn_policy.maxTtl = None

  if args.negative_caching is not None:
    cdn_policy.negativeCaching = args.negative_caching
  negative_caching_policy = GetNegativeCachingPolicy(client, args,
                                                     backend_bucket)
  if negative_caching_policy is not None:
    cdn_policy.negativeCachingPolicy = negative_caching_policy
  if args.negative_caching_policy:
    cdn_policy.negativeCaching = True

  if is_update:
    if (args.no_negative_caching_policies or
        (args.negative_caching is not None and not args.negative_caching)):
      cleared_fields.append('cdnPolicy.negativeCachingPolicy')
      cdn_policy.negativeCachingPolicy = []

  if args.serve_while_stale is not None:
    cdn_policy.serveWhileStale = args.serve_while_stale

  bypass_cache_on_request_headers = GetBypassCacheOnRequestHeaders(client, args)
  if bypass_cache_on_request_headers is not None:
    cdn_policy.bypassCacheOnRequestHeaders = bypass_cache_on_request_headers

  if is_update:
    if args.no_serve_while_stale:
      cleared_fields.append('cdnPolicy.serveWhileStale')
      cdn_policy.serveWhileStale = None
    if args.no_bypass_cache_on_request_headers:
      cleared_fields.append('cdnPolicy.bypassCacheOnRequestHeaders')
      cdn_policy.bypassCacheOnRequestHeaders = []

  if HasCacheKeyPolicyArgs(args):
    cdn_policy.cacheKeyPolicy = GetCacheKeyPolicy(client, args, backend_bucket)

  if cdn_policy != client.messages.BackendBucketCdnPolicy():
    backend_bucket.cdnPolicy = cdn_policy
