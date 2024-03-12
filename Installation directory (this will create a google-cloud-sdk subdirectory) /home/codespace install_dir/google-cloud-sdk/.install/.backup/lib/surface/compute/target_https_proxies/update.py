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
"""Command for updating target HTTPS proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
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
      'brief': 'Update a target HTTPS proxy.',
      'DESCRIPTION': """
      *{command}* is used to change the SSL certificate and/or URL map of
      existing target HTTPS proxies. A target HTTPS proxy is referenced by
      one or more forwarding rules which specify the network traffic that
      the proxy is responsible for routing. The target HTTPS proxy in turn
      points to a URL map that defines the rules for routing the requests.
      The URL map's job is to map URLs to backend services which handle
      the actual requests. The target HTTPS proxy also points to at most
      15 SSL certificates used for server-side authentication. The target
      HTTPS proxy can be associated with at most one SSL policy.
      """,
      'EXAMPLES': """
      Update the URL map of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP

      Update the SSL certificate of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --ssl-certificates=SSL_CERTIFIFCATE

      Update the URL map of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --region=REGION_NAME

      Update the SSL certificate of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --ssl-certificates=SSL_CERTIFIFCATE --region=REGION_NAME
      """,
  }


def _CheckMissingArgument(args, server_tls_policy_enabled):
  """Checks for missing argument."""
  server_tls_policy_args = [
      'clear_server_tls_policy',
      'server_tls_policy',
  ]
  all_args = [
      'ssl_certificates',
      'url_map',
      'quic_override',
      'ssl_policy',
      'clear_ssl_policy',
      'certificate_map',
      'clear_certificate_map',
      'clear_ssl_certificates',
      'certificate_manager_certificates',
      'clear_http_keep_alive_timeout_sec',
      'http_keep_alive_timeout_sec',
  ] + (server_tls_policy_args if server_tls_policy_enabled else [])
  err_server_tls_policy_args = [
      '[--clear-server-tls-policy]',
      '[--server-tls-policy]',
  ]
  err_msg_args = [
      '[--ssl-certificates]',
      '[--url-map]',
      '[--quic-override]',
      '[--ssl-policy]',
      '[--clear-ssl-policy]',
      '[--certificate-map]',
      '[--clear-certificate-map]',
      '[--clear-ssl-certificates]',
      '[--certificate-manager-certificates]',
      '[--clear-http-keep-alive-timeout-sec]',
      '[--http-keep-alive-timeout-sec]',
  ] + (err_server_tls_policy_args if server_tls_policy_enabled else [])
  if not sum(args.IsSpecified(arg) for arg in all_args):
    raise compute_exceptions.ArgumentError(
        'You must specify at least one of %s or %s.'
        % (', '.join(err_msg_args[:-1]), err_msg_args[-1])
    )


def _Run(
    args,
    holder,
    ssl_certificates_arg,
    target_https_proxy_arg,
    url_map_arg,
    ssl_policy_arg,
    certificate_map_ref,
    server_tls_policy_enabled,
):
  """Issues requests necessary to update Target HTTPS Proxies."""
  client = holder.client

  proxy_ref = target_https_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client),
  )

  old_resource = _GetTargetHttpsProxy(client, proxy_ref)
  new_resource = encoding.CopyProtoMessage(old_resource)
  cleared_fields = []

  clear_ssl_certificates = args.IsKnownAndSpecified('clear_ssl_certificates')
  if args.ssl_certificates or clear_ssl_certificates:
    new_resource.sslCertificates = []
    if args.ssl_certificates:
      ssl_cert_refs = target_https_proxies_utils.ResolveSslCertificates(
          args, ssl_certificates_arg, proxy_ref, holder.resources
      )
      new_resource.sslCertificates = [ref.SelfLink() for ref in ssl_cert_refs]
    if clear_ssl_certificates:
      cleared_fields.append('sslCertificates')
  elif args.certificate_manager_certificates:
    location = target_https_proxies_utils.GetLocation(proxy_ref)
    ssl_cert_refs = [
        reference_utils.BuildCcmCertificateUrl(
            proxy_ref.project, location, certificate_name
        )
        for certificate_name in args.certificate_manager_certificates
    ]
    new_resource.sslCertificates = ssl_cert_refs

  if args.url_map:
    new_resource.urlMap = (
        target_https_proxies_utils.ResolveTargetHttpsProxyUrlMap(
            args, url_map_arg, proxy_ref, holder.resources
        ).SelfLink()
    )

  if args.quic_override:
    new_resource.quicOverride = (
        client.messages.TargetHttpsProxy.QuicOverrideValueValuesEnum(
            args.quic_override
        )
    )

  if args.ssl_policy:
    ssl_policy_ref = target_https_proxies_utils.ResolveSslPolicy(
        args, ssl_policy_arg, proxy_ref, holder.resources
    )
    new_resource.sslPolicy = ssl_policy_ref.SelfLink()

  if args.IsSpecified('clear_ssl_policy'):
    new_resource.sslPolicy = None
    cleared_fields.append('sslPolicy')

  if args.IsSpecified('http_keep_alive_timeout_sec'):
    new_resource.httpKeepAliveTimeoutSec = args.http_keep_alive_timeout_sec
  elif args.IsSpecified('clear_http_keep_alive_timeout_sec'):
    new_resource.httpKeepAliveTimeoutSec = None
    cleared_fields.append('httpKeepAliveTimeoutSec')

  if certificate_map_ref:
    new_resource.certificateMap = certificate_map_ref.SelfLink()

  if args.IsKnownAndSpecified('clear_certificate_map'):
    new_resource.certificateMap = None
    cleared_fields.append('certificateMap')

  if server_tls_policy_enabled:
    if args.IsKnownAndSpecified('server_tls_policy'):
      server_tls_policy_ref = args.CONCEPTS.server_tls_policy.Parse()
      new_resource.serverTlsPolicy = server_tls_policy_ref.SelfLink()
    elif args.IsKnownAndSpecified('clear_server_tls_policy'):
      new_resource.serverTlsPolicy = None
      cleared_fields.append('serverTlsPolicy')

  if old_resource != new_resource:
    return _PatchTargetHttpsProxy(
        client, proxy_ref, new_resource, cleared_fields
    )
  return []


def _GetTargetHttpsProxy(client, proxy_ref):
  """Retrieves the target HTTPS proxy."""
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(proxy_ref):
    request = client.messages.ComputeRegionTargetHttpsProxiesGetRequest(
        **proxy_ref.AsDict()
    )
    collection = client.apitools_client.regionTargetHttpsProxies
  else:
    request = client.messages.ComputeTargetHttpsProxiesGetRequest(
        **proxy_ref.AsDict()
    )
    collection = client.apitools_client.targetHttpsProxies
  return client.MakeRequests([(collection, 'Get', request)])[0]


def _PatchTargetHttpsProxy(client, proxy_ref, new_resource, cleared_fields):
  """Patches the target HTTPS proxy."""
  requests = []
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(proxy_ref):
    requests.append((
        client.apitools_client.regionTargetHttpsProxies,
        'Patch',
        client.messages.ComputeRegionTargetHttpsProxiesPatchRequest(
            project=proxy_ref.project,
            region=proxy_ref.region,
            targetHttpsProxy=proxy_ref.Name(),
            targetHttpsProxyResource=new_resource,
        ),
    ))
  else:
    requests.append((
        client.apitools_client.targetHttpsProxies,
        'Patch',
        client.messages.ComputeTargetHttpsProxiesPatchRequest(
            project=proxy_ref.project,
            targetHttpsProxy=proxy_ref.Name(),
            targetHttpsProxyResource=new_resource,
        ),
    ))
  with client.apitools_client.IncludeFields(cleared_fields):
    return client.MakeRequests(requests)


def _AddServerTLSPolicyArguments(parser):
  """Adds all Server TLS Policy-related arguments."""
  server_tls_group = parser.add_mutually_exclusive_group()
  ns_resource_args.GetServerTlsPolicyResourceArg(
      'to attach',
      name='server-tls-policy',
      group=server_tls_group,
      region_fallthrough=True,
  ).AddToParser(server_tls_group)
  ns_resource_args.GetClearServerTLSPolicyForHttpsProxy().AddToParser(
      server_tls_group
  )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a target HTTPS proxy."""

  SSL_CERTIFICATES_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None
  SSL_POLICY_ARG = None
  detailed_help = _DetailedHelp()
  _server_tls_policy_enabled = False

  @classmethod
  def Args(cls, parser):
    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target HTTPS proxy', required=False
        )
    )

    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument()
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='update')

    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        required=False, proxy_type='HTTPS'
    )
    cls.URL_MAP_ARG.AddArgument(parser)

    group = parser.add_mutually_exclusive_group()
    certificate_group = group.add_argument_group()
    cert_main_flags_group = certificate_group.add_mutually_exclusive_group()
    cls.SSL_CERTIFICATES_ARG.AddArgument(
        certificate_group,
        mutex_group=cert_main_flags_group,
        cust_metavar='SSL_CERTIFICATE',
    )
    resource_args.AddCertificateResourceArg(
        parser,
        'to attach',
        noun='certificate-manager-certificates',
        name='certificate-manager-certificates',
        positional=False,
        required=False,
        plural=True,
        group=cert_main_flags_group,
        with_location=False,
    )
    ssl_certificates_flags.GetClearSslCertificatesArgumentForOtherResource(
        'HTTPS'
    ).AddToParser(cert_main_flags_group)
    map_group = group.add_mutually_exclusive_group()
    resource_args.AddCertificateMapResourceArg(
        map_group,
        'to attach',
        name='certificate-map',
        positional=False,
        required=False,
        with_location=False,
    )
    resource_args.GetClearCertificateMapArgumentForOtherResource(
        'HTTPS proxy'
    ).AddToParser(map_group)

    cls.SSL_POLICY_ARG = (
        ssl_policies_flags.GetSslPolicyMultiScopeArgumentForOtherResource(
            'HTTPS', required=False
        )
    )

    group = parser.add_mutually_exclusive_group()
    ssl_policy_group = group.add_argument_group()
    cls.SSL_POLICY_ARG.AddArgument(ssl_policy_group)

    ssl_policies_flags.GetClearSslPolicyArgumentForOtherResource(
        'HTTPS', required=False
    ).AddToParser(group)

    group = parser.add_mutually_exclusive_group()
    target_proxies_utils.AddHttpKeepAliveTimeoutSec(group)
    target_proxies_utils.AddClearHttpKeepAliveTimeoutSec(group)

    target_proxies_utils.AddQuicOverrideUpdateArgs(parser)
    if cls._server_tls_policy_enabled:
      _AddServerTLSPolicyArguments(parser)

  def Run(self, args):
    _CheckMissingArgument(args, self._server_tls_policy_enabled)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    certificate_map_ref = args.CONCEPTS.certificate_map.Parse()
    return _Run(
        args,
        holder,
        self.SSL_CERTIFICATES_ARG,
        self.TARGET_HTTPS_PROXY_ARG,
        self.URL_MAP_ARG,
        self.SSL_POLICY_ARG,
        certificate_map_ref,
        self._server_tls_policy_enabled,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateBeta(Update):
  _server_tls_policy_enabled = True
