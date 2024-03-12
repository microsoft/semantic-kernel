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
"""Command for creating target HTTPS proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args as cm_resource_args
from googlecloudsdk.command_lib.compute import reference_utils
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_certificates import flags as ssl_certificates_flags
from googlecloudsdk.command_lib.compute.ssl_policies import flags as ssl_policies_flags
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.target_https_proxies import target_https_proxies_utils
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags
from googlecloudsdk.command_lib.network_security import resource_args as ns_resource_args


def _DetailedHelp():
  return {
      'brief': 'Create a target HTTPS proxy.',
      'DESCRIPTION': """
      *{command}* is used to create target HTTPS proxies. A target
      HTTPS proxy is referenced by one or more forwarding rules which
      specify the network traffic that the proxy is responsible for
      routing. The target HTTPS proxy points to a URL map that defines
      the rules for routing the requests. The URL map's job is to map
      URLs to backend services which handle the actual requests. The
      target HTTPS proxy also points to at most 15 SSL certificates
      used for server-side authentication. The target HTTPS proxy can
      be associated with at most one SSL policy.
      """,
      'EXAMPLES': """
      If there is an already-created URL map with the name URL_MAP
      and a SSL certificate named SSL_CERTIFICATE, create a
      global target HTTPS proxy pointing to this map by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --ssl-certificates=SSL_CERTIFICATE

      Create a regional target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --ssl-certificates=SSL_CERTIFICATE --region=REGION_NAME
      """,
  }


def _Args(
    parser,
    traffic_director_security=False,
    certificate_map=False,
    server_tls_policy_enabled=False,
    list_format=None,
):
  """Add the target https proxies command line flags to the parser."""

  parser.display_info.AddFormat(list_format)
  parser.add_argument(
      '--description',
      help='An optional, textual description for the target HTTPS proxy.',
  )

  parser.display_info.AddCacheUpdater(flags.TargetHttpsProxiesCompleter)
  target_proxies_utils.AddQuicOverrideCreateArgs(parser)

  if traffic_director_security:
    flags.AddProxyBind(parser, False)

  target_proxies_utils.AddHttpKeepAliveTimeoutSec(parser)

  if server_tls_policy_enabled:
    ns_resource_args.GetServerTlsPolicyResourceArg(
        'to attach', name='server-tls-policy', region_fallthrough=True
    ).AddToParser(parser)

  if certificate_map:
    cm_resource_args.AddCertificateMapResourceArg(
        parser,
        'to attach',
        name='certificate-map',
        positional=False,
        required=False,
        with_location=False,
    )


def _Run(
    args,
    holder,
    proxy_ref,
    url_map_ref,
    ssl_certificates,
    ssl_policy_ref,
    traffic_director_security,
    certificate_map_ref,
    server_tls_policy_ref,
):
  """Issues requests necessary to create Target HTTPS Proxies."""
  client = holder.client

  if traffic_director_security and args.proxy_bind:
    target_https_proxy = client.messages.TargetHttpsProxy(
        description=args.description,
        name=proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
        sslCertificates=ssl_certificates,
        proxyBind=args.proxy_bind,
    )
  else:
    target_https_proxy = client.messages.TargetHttpsProxy(
        description=args.description,
        name=proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
        sslCertificates=ssl_certificates,
    )

  if args.IsSpecified('http_keep_alive_timeout_sec'):
    target_https_proxy.httpKeepAliveTimeoutSec = (
        args.http_keep_alive_timeout_sec
    )

  if args.IsSpecified('quic_override'):
    quic_enum = client.messages.TargetHttpsProxy.QuicOverrideValueValuesEnum
    target_https_proxy.quicOverride = quic_enum(args.quic_override)

  if ssl_policy_ref:
    target_https_proxy.sslPolicy = ssl_policy_ref.SelfLink()

  if server_tls_policy_ref:
    target_https_proxy.serverTlsPolicy = server_tls_policy_ref.SelfLink()

  if certificate_map_ref:
    target_https_proxy.certificateMap = certificate_map_ref.SelfLink()

  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(proxy_ref):
    request = client.messages.ComputeRegionTargetHttpsProxiesInsertRequest(
        project=proxy_ref.project,
        region=proxy_ref.region,
        targetHttpsProxy=target_https_proxy,
    )
    collection = client.apitools_client.regionTargetHttpsProxies
  else:
    request = client.messages.ComputeTargetHttpsProxiesInsertRequest(
        project=proxy_ref.project, targetHttpsProxy=target_https_proxy
    )
    collection = client.apitools_client.targetHttpsProxies

  return client.MakeRequests([(collection, 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a target HTTPS proxy."""

  _traffic_director_security = False
  _certificate_map = True
  _server_tls_policy_enabled = False
  _list_format = flags.DEFAULT_LIST_FORMAT

  SSL_CERTIFICATES_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None
  SSL_POLICY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    certificate_group = parser.add_mutually_exclusive_group()
    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target HTTPS proxy', required=False
        )
    )
    cls.SSL_CERTIFICATES_ARG.AddArgument(
        parser, mutex_group=certificate_group, cust_metavar='SSL_CERTIFICATE'
    )
    cm_resource_args.AddCertificateResourceArg(
        parser,
        'to attach',
        noun='certificate-manager-certificates',
        name='certificate-manager-certificates',
        positional=False,
        required=False,
        plural=True,
        group=certificate_group,
        with_location=False,
    )

    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument()
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='create')

    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        proxy_type='HTTPS'
    )
    cls.URL_MAP_ARG.AddArgument(parser)

    cls.SSL_POLICY_ARG = (
        ssl_policies_flags.GetSslPolicyMultiScopeArgumentForOtherResource(
            'HTTPS', required=False
        )
    )
    cls.SSL_POLICY_ARG.AddArgument(parser)

    _Args(
        parser,
        traffic_director_security=cls._traffic_director_security,
        certificate_map=cls._certificate_map,
        server_tls_policy_enabled=cls._server_tls_policy_enabled,
        list_format=cls._list_format,
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    proxy_ref = self.TARGET_HTTPS_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL
    )
    url_map_ref = target_https_proxies_utils.ResolveTargetHttpsProxyUrlMap(
        args, self.URL_MAP_ARG, proxy_ref, holder.resources
    )
    ssl_certificates = target_https_proxies_utils.ResolveSslCertificates(
        args, self.SSL_CERTIFICATES_ARG, proxy_ref, holder.resources
    )
    location = target_https_proxies_utils.GetLocation(proxy_ref)
    if ssl_certificates:
      ssl_certificates = [ref.SelfLink() for ref in ssl_certificates]
    elif args.certificate_manager_certificates:
      ssl_certificates = [
          reference_utils.BuildCcmCertificateUrl(
              proxy_ref.project, location, certificate_name
          )
          for certificate_name in args.certificate_manager_certificates
      ]
    if args.ssl_policy:
      ssl_policy_ref = target_https_proxies_utils.ResolveSslPolicy(
          args, self.SSL_POLICY_ARG, proxy_ref, holder.resources
      )
    else:
      ssl_policy_ref = None
    certificate_map_ref = (
        args.CONCEPTS.certificate_map.Parse() if self._certificate_map else None
    )
    server_tls_policy_ref = None
    if self._server_tls_policy_enabled and args.IsKnownAndSpecified(
        'server_tls_policy'
    ):
      server_tls_policy_ref = args.CONCEPTS.server_tls_policy.Parse()
    return _Run(
        args,
        holder,
        proxy_ref,
        url_map_ref,
        ssl_certificates,
        ssl_policy_ref,
        self._traffic_director_security,
        certificate_map_ref,
        server_tls_policy_ref,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  _server_tls_policy_enabled = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  _traffic_director_security = True
