# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple target-https-proxies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import scope as compute_scope


def ResolveTargetHttpsProxyUrlMap(args, url_map_arg, target_https_proxy_ref,
                                  resources):
  """Parses the URL map that is pointed to by a Target HTTPS Proxy from args.

  This function handles parsing a regional/global URL map that is
  pointed to by a regional/global Target HTTPS Proxy.

  Args:
    args: The arguments provided to the target_https_proxies command.
    url_map_arg: The ResourceArgument specification for the url map argument.
    target_https_proxy_ref: The resource reference to the Target HTTPS Proxy.
                            This is obtained by parsing the Target HTTPS Proxy
                            arguments provided.
    resources: ComputeApiHolder resources.

  Returns:
    Returns the URL map resource
  """

  if not compute_scope.IsSpecifiedForFlag(args, 'url_map'):
    if IsRegionalTargetHttpsProxiesRef(target_https_proxy_ref):
      args.url_map_region = target_https_proxy_ref.region
    else:
      args.global_url_map = bool(args.url_map)

  return url_map_arg.ResolveAsResource(args, resources)


def ResolveSslCertificates(args, ssl_certificate_arg, target_https_proxy_ref,
                           resources):
  """Parses the ssl certs that are pointed to by a Target HTTPS Proxy from args.

  This function handles parsing regional/global ssl certificates that are
  pointed to by a regional/global Target HTTPS Proxy.

  Args:
    args: The arguments provided to the target_https_proxies command.
    ssl_certificate_arg: The ResourceArgument specification for the
                         ssl_certificates argument.
    target_https_proxy_ref: The resource reference to the Target HTTPS Proxy.
                            This is obtained by parsing the Target HTTPS Proxy
                            arguments provided.
    resources: ComputeApiHolder resources.

  Returns:
    Returns the SSL Certificates resource
  """

  if not args.ssl_certificates:
    return []

  if not compute_scope.IsSpecifiedForFlag(args, 'ssl_certificates'):
    if IsRegionalTargetHttpsProxiesRef(target_https_proxy_ref):
      args.ssl_certificates_region = target_https_proxy_ref.region
    else:
      args.global_ssl_certificates = bool(args.ssl_certificates)
  return ssl_certificate_arg.ResolveAsResource(args, resources)


def ResolveSslPolicy(args, ssl_policy_arg, target_https_proxy_ref, resources):
  """Parses the SSL policies that are pointed to by a Target HTTPS Proxy from args.

  This function handles parsing regional/global SSL policies that are
  pointed to by a regional/global Target HTTPS Proxy.

  Args:
    args: The arguments provided to the target_https_proxies command.
    ssl_policy_arg: The ResourceArgument specification for the ssl_policies
      argument.
    target_https_proxy_ref: The resource reference to the Target HTTPS Proxy.
      This is obtained by parsing the Target HTTPS Proxy arguments provided.
    resources: ComputeApiHolder resources.

  Returns:
    Returns the SSL policy resource
  """

  if not compute_scope.IsSpecifiedForFlag(args, 'ssl_policy'):
    if IsRegionalTargetHttpsProxiesRef(target_https_proxy_ref):
      args.ssl_policy_region = target_https_proxy_ref.region
    else:
      args.global_ssl_policy = bool(args.ssl_policy)
  return ssl_policy_arg.ResolveAsResource(args, resources)


def IsRegionalTargetHttpsProxiesRef(target_https_proxy_ref):
  """Returns True if the Target HTTPS Proxy reference is regional."""

  return target_https_proxy_ref.Collection() == \
         'compute.regionTargetHttpsProxies'


def IsGlobalTargetHttpsProxiesRef(target_https_proxy_ref):
  """Returns True if the Target HTTPS Proxy reference is global."""

  return target_https_proxy_ref.Collection() == 'compute.targetHttpsProxies'


def GetLocation(target_https_proxy_ref):
  """Transforms compute global/region of Target HTTPS Proxy to location."""
  if IsRegionalTargetHttpsProxiesRef(target_https_proxy_ref):
    return target_https_proxy_ref.region
  return 'global'


def SendGetRequest(client, target_https_proxy_ref):
  """Send Url Maps get request."""
  if target_https_proxy_ref.Collection() == 'compute.regionTargetHttpsProxies':
    return client.apitools_client.regionTargetHttpsProxies.Get(
        client.messages.ComputeRegionTargetHttpsProxiesGetRequest(
            **target_https_proxy_ref.AsDict()))
  return client.apitools_client.targetHttpsProxies.Get(
      client.messages.ComputeTargetHttpsProxiesGetRequest(
          **target_https_proxy_ref.AsDict()))
