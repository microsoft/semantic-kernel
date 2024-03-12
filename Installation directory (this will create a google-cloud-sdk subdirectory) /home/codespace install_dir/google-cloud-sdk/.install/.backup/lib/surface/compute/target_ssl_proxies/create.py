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
"""Command for creating target SSL proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificates_flags)
from googlecloudsdk.command_lib.compute.ssl_policies import (flags as
                                                             ssl_policies_flags)
from googlecloudsdk.command_lib.compute.target_ssl_proxies import flags
from googlecloudsdk.command_lib.compute.target_ssl_proxies import target_ssl_proxies_utils


class Create(base.CreateCommand):
  """Create a target SSL proxy.

  *{command}* is used to create target SSL proxies. A target SSL proxy is
  referenced by one or more forwarding rules which define which packets the
  proxy is responsible for routing. The target SSL proxy points to a backend
  service which handle the actual requests. The target SSL proxy also points
  to at most 15 SSL certificates used for server-side authentication or one
  certificate map. The target SSL proxy can be associated with at most one SSL
  policy.
  """

  _certificate_map = True
  _list_format = flags.DEFAULT_LIST_FORMAT

  BACKEND_SERVICE_ARG = None
  SSL_CERTIFICATES_ARG = None
  TARGET_SSL_PROXY_ARG = None
  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    target_proxies_utils.AddProxyHeaderRelatedCreateArgs(parser)

    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForTargetSslProxy())
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.TARGET_SSL_PROXY_ARG = flags.TargetSslProxyArgument()
    cls.TARGET_SSL_PROXY_ARG.AddArgument(parser, operation_type='create')

    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target SSL proxy',
            required=not cls._certificate_map,
            include_regional_ssl_certificates=False))
    if not cls._certificate_map:
      cls.SSL_CERTIFICATES_ARG.AddArgument(
          parser, cust_metavar='SSL_CERTIFICATE')

    cls.SSL_POLICY_ARG = ssl_policies_flags.GetSslPolicyMultiScopeArgumentForOtherResource(
        'SSL', required=False)
    cls.SSL_POLICY_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help='An optional, textual description for the target SSL proxy.')

    parser.display_info.AddCacheUpdater(flags.TargetSslProxiesCompleter)
    parser.display_info.AddFormat(cls._list_format)

    if cls._certificate_map:
      group = parser.add_argument_group(required=True)
      cls.SSL_CERTIFICATES_ARG.AddArgument(
          group, cust_metavar='SSL_CERTIFICATE')
      resource_args.AddCertificateMapResourceArg(
          group,
          'to attach',
          name='certificate-map',
          positional=False,
          required=False,
          with_location=False)

  def _CreateResource(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    backend_service_ref = self.BACKEND_SERVICE_ARG.ResolveAsResource(
        args, holder.resources)

    target_ssl_proxy_ref = self.TARGET_SSL_PROXY_ARG.ResolveAsResource(
        args, holder.resources)

    ssl_cert_refs = None
    if args.ssl_certificates:
      ssl_cert_refs = self.SSL_CERTIFICATES_ARG.ResolveAsResource(
          args, holder.resources)

    client = holder.client.apitools_client
    messages = holder.client.messages
    if args.proxy_header:
      proxy_header = messages.TargetSslProxy.ProxyHeaderValueValuesEnum(
          args.proxy_header)
    else:
      proxy_header = (messages.TargetSslProxy.ProxyHeaderValueValuesEnum.NONE)

    target_ssl_proxy = messages.TargetSslProxy(
        description=args.description,
        name=target_ssl_proxy_ref.Name(),
        proxyHeader=proxy_header,
        service=backend_service_ref.SelfLink())

    if ssl_cert_refs:
      target_ssl_proxy.sslCertificates = [
          ref.SelfLink() for ref in ssl_cert_refs
      ]

    if args.ssl_policy:
      target_ssl_proxy.sslPolicy = target_ssl_proxies_utils.ResolveSslPolicy(
          args, self.SSL_POLICY_ARG, target_ssl_proxy_ref,
          holder.resources).SelfLink()

    if self._certificate_map:
      certificate_map_ref = args.CONCEPTS.certificate_map.Parse()
      if certificate_map_ref:
        target_ssl_proxy.certificateMap = certificate_map_ref.SelfLink()

    request = messages.ComputeTargetSslProxiesInsertRequest(
        project=target_ssl_proxy_ref.project, targetSslProxy=target_ssl_proxy)

    errors = []
    resources = holder.client.MakeRequests(
        [(client.targetSslProxies, 'Insert', request)], errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources

  def Run(self, args):
    return self._CreateResource(args)
