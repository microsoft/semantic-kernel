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
"""Command for updating target SSL proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificates_flags)
from googlecloudsdk.command_lib.compute.ssl_policies import (flags as
                                                             ssl_policies_flags)
from googlecloudsdk.command_lib.compute.target_ssl_proxies import flags
from googlecloudsdk.command_lib.compute.target_ssl_proxies import target_ssl_proxies_utils


class Update(base.SilentCommand):
  """Update a target SSL proxy.

  *{command}* is used to replace the SSL certificate, backend service, proxy
  header or SSL policy of existing target SSL proxies. A target SSL proxy is
  referenced by one or more forwarding rules which define which packets the
  proxy is responsible for routing. The target SSL proxy in turn points to a
  backend service which will handle the requests. The target SSL proxy also
  points to at most 15 SSL certificates used for server-side authentication
  or one certificate map. The target SSL proxy can be associated with at most
  one SSL policy.
  """

  _certificate_map = True

  BACKEND_SERVICE_ARG = None
  SSL_CERTIFICATES_ARG = None
  TARGET_SSL_PROXY_ARG = None
  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    target_proxies_utils.AddProxyHeaderRelatedUpdateArgs(parser)

    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForTargetSslProxy(
            required=False))
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.TARGET_SSL_PROXY_ARG = flags.TargetSslProxyArgument()
    cls.TARGET_SSL_PROXY_ARG.AddArgument(parser, operation_type='update')
    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target SSL proxy',
            required=False,
            include_regional_ssl_certificates=False))
    if not cls._certificate_map:
      cls.SSL_CERTIFICATES_ARG.AddArgument(
          parser, cust_metavar='SSL_CERTIFICATE')

    cls.SSL_POLICY_ARG = (
        ssl_policies_flags.GetSslPolicyMultiScopeArgumentForOtherResource(
            'SSL', required=False))

    group = parser.add_mutually_exclusive_group()
    ssl_policy_group = group.add_argument_group()
    cls.SSL_POLICY_ARG.AddArgument(ssl_policy_group)

    ssl_policies_flags.GetClearSslPolicyArgumentForOtherResource(
        'SSL', required=False).AddToParser(group)
    if cls._certificate_map:
      group = parser.add_mutually_exclusive_group(sort_args=False)
      cls.SSL_CERTIFICATES_ARG.AddArgument(
          group, cust_metavar='SSL_CERTIFICATE')
      ssl_certificates_flags.GetClearSslCertificatesArgumentForOtherResource(
          'SSL').AddToParser(group)
      resource_args.AddCertificateMapResourceArg(
          group,
          'to attach',
          name='certificate-map',
          positional=False,
          required=False,
          with_location=False)
      resource_args.GetClearCertificateMapArgumentForOtherResource(
          'SSL proxy').AddToParser(group)

  def _SendRequests(self,
                    args,
                    ssl_policy=None,
                    clear_ssl_policy=False,
                    certificate_map_ref=None):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    requests = []
    target_ssl_proxy_ref = self.TARGET_SSL_PROXY_ARG.ResolveAsResource(
        args, holder.resources)

    client = holder.client.apitools_client
    messages = holder.client.messages

    clear_ssl_certificates = args.IsKnownAndSpecified('clear_ssl_certificates')
    if args.ssl_certificates or clear_ssl_certificates:
      ssl_certs = []
      if args.ssl_certificates:
        ssl_cert_refs = self.SSL_CERTIFICATES_ARG.ResolveAsResource(
            args, holder.resources)
        ssl_certs = [ref.SelfLink() for ref in ssl_cert_refs]
      requests.append(
          (client.targetSslProxies, 'SetSslCertificates',
           messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
               project=target_ssl_proxy_ref.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetSslCertificatesRequest=(
                   messages.TargetSslProxiesSetSslCertificatesRequest(
                       sslCertificates=ssl_certs)))))

    if args.backend_service:
      backend_service_ref = self.BACKEND_SERVICE_ARG.ResolveAsResource(
          args, holder.resources)
      requests.append(
          (client.targetSslProxies, 'SetBackendService',
           messages.ComputeTargetSslProxiesSetBackendServiceRequest(
               project=target_ssl_proxy_ref.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetBackendServiceRequest=(
                   messages.TargetSslProxiesSetBackendServiceRequest(
                       service=backend_service_ref.SelfLink())))))

    if args.proxy_header:
      proxy_header = (
          messages.TargetSslProxiesSetProxyHeaderRequest
          .ProxyHeaderValueValuesEnum(args.proxy_header))
      requests.append((client.targetSslProxies, 'SetProxyHeader',
                       messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
                           project=target_ssl_proxy_ref.project,
                           targetSslProxy=target_ssl_proxy_ref.Name(),
                           targetSslProxiesSetProxyHeaderRequest=(
                               messages.TargetSslProxiesSetProxyHeaderRequest(
                                   proxyHeader=proxy_header)))))
    if args.ssl_policy:
      ssl_policy_ref = target_ssl_proxies_utils.ResolveSslPolicy(
          args, self.SSL_POLICY_ARG, target_ssl_proxy_ref, holder.resources)
      ssl_policy = messages.SslPolicyReference(
          sslPolicy=ssl_policy_ref.SelfLink())
    else:
      ssl_policy = None
    clear_ssl_policy = args.clear_ssl_policy

    if ssl_policy or clear_ssl_policy:
      requests.append((client.targetSslProxies, 'SetSslPolicy',
                       messages.ComputeTargetSslProxiesSetSslPolicyRequest(
                           project=target_ssl_proxy_ref.project,
                           targetSslProxy=target_ssl_proxy_ref.Name(),
                           sslPolicyReference=ssl_policy)))

    clear_certificate_map = args.IsKnownAndSpecified('clear_certificate_map')
    certificate_map_ref = args.CONCEPTS.certificate_map.Parse(
    ) if self._certificate_map else None
    if certificate_map_ref or clear_certificate_map:
      self_link = certificate_map_ref.SelfLink(
      ) if certificate_map_ref else None
      requests.append((client.targetSslProxies, 'SetCertificateMap',
                       messages.ComputeTargetSslProxiesSetCertificateMapRequest(
                           project=target_ssl_proxy_ref.project,
                           targetSslProxy=target_ssl_proxy_ref.Name(),
                           targetSslProxiesSetCertificateMapRequest=messages
                           .TargetSslProxiesSetCertificateMapRequest(
                               certificateMap=self_link))))

    errors = []
    resources = holder.client.MakeRequests(requests, errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources

  def _CheckMissingArgument(self, args):
    """Checks for missing argument."""
    all_args = [
        'ssl_certificates', 'proxy_header', 'backend_service', 'ssl_policy',
        'clear_ssl_policy'
    ]
    err_msg_args = [
        '[--ssl-certificates]', '[--backend-service]', '[--proxy-header]',
        '[--ssl-policy]', '[--clear-ssl-policy]'
    ]
    if self._certificate_map:
      all_args.append('certificate_map')
      err_msg_args.append('[--certificate-map]')
      all_args.append('clear_certificate_map')
      err_msg_args.append('[--clear-certificate-map]')
      all_args.append('clear_ssl_certificates')
      err_msg_args.append('[--clear-ssl-certificates]')
    if not sum(args.IsSpecified(arg) for arg in all_args):
      raise compute_exceptions.UpdatePropertyError(
          'You must specify at least one of %s or %s.' %
          (', '.join(err_msg_args[:-1]), err_msg_args[-1]))

  def Run(self, args):
    self._CheckMissingArgument(args)
    return self._SendRequests(args)
