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
"""Command for creating backend services.

   There are separate alpha, beta, and GA command classes in this file.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import cdn_flags_utils as cdn_flags
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import reference_utils
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import log


def _ResolvePortName(args):
  """Determine port name if one was not specified."""
  if args.port_name:
    return args.port_name

  def _LogAndReturn(port_name):
    log.status.Print('Backend-services\' port_name automatically resolved to '
                     '{} based on the service protocol.'.format(port_name))
    return port_name

  if args.protocol == 'HTTPS':
    return _LogAndReturn('https')
  if args.protocol == 'HTTP2':
    return _LogAndReturn('http2')
  if args.protocol == 'SSL':
    return _LogAndReturn('ssl')
  if args.protocol == 'TCP':
    return _LogAndReturn('tcp')

  return 'http'


def _ResolveProtocol(messages, args, default='HTTP'):
  valid_options = messages.BackendService.ProtocolValueValuesEnum.names()
  if args.protocol and args.protocol not in valid_options:
    raise ValueError('{} is not a supported option. See the help text of '
                     '--protocol for supported options.'.format(args.protocol))
  return messages.BackendService.ProtocolValueValuesEnum(args.protocol or
                                                         default)


def AddIapFlag(parser):
  # TODO(b/34479878): It would be nice if the auto-generated help text were
  # a bit better so we didn't need to be quite so verbose here.
  flags.AddIap(
      parser,
      help="""\
      Configure Identity Aware Proxy (IAP) for external HTTP(S) load balancing.
      You can configure IAP to be `enabled` or `disabled` (default). If enabled,
      you can provide values for `oauth2-client-id` and `oauth2-client-secret`.
      For example, `--iap=enabled,oauth2-client-id=foo,oauth2-client-secret=bar`
      turns IAP on, and `--iap=disabled` turns it off. For more information, see
      https://cloud.google.com/iap/.
      """)


class CreateHelper(object):
  """Helper class to create a backend service."""

  HEALTH_CHECK_ARG = None
  HTTP_HEALTH_CHECK_ARG = None
  HTTPS_HEALTH_CHECK_ARG = None

  @classmethod
  def Args(
      cls,
      parser,
      support_failover,
      support_multinic,
      support_client_only,
      support_unspecified_protocol,
      support_subsetting,
      support_subsetting_subset_size,
      support_advanced_load_balancing,
      support_ip_address_selection_policy,
  ):
    """Add flags to create a backend service to the parser."""

    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(
        parser, operation_type='create')
    flags.AddDescription(parser)
    cls.HEALTH_CHECK_ARG = flags.HealthCheckArgument()
    cls.HEALTH_CHECK_ARG.AddArgument(parser, cust_metavar='HEALTH_CHECK')
    cls.HTTP_HEALTH_CHECK_ARG = flags.HttpHealthCheckArgument()
    cls.HTTP_HEALTH_CHECK_ARG.AddArgument(
        parser, cust_metavar='HTTP_HEALTH_CHECK')
    cls.HTTPS_HEALTH_CHECK_ARG = flags.HttpsHealthCheckArgument()
    cls.HTTPS_HEALTH_CHECK_ARG.AddArgument(
        parser, cust_metavar='HTTPS_HEALTH_CHECK')
    if support_advanced_load_balancing:
      flags.AddServiceLoadBalancingPolicy(parser)
    flags.AddServiceBindings(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(
        parser,
        default=None,
        support_unspecified_protocol=support_unspecified_protocol)
    flags.AddEnableCdn(parser)
    flags.AddSessionAffinity(parser, support_client_only=support_client_only)
    flags.AddAffinityCookieTtl(parser)
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddLoadBalancingScheme(parser)
    flags.AddCustomRequestHeaders(parser, remove_all_flag=False)
    flags.AddCacheKeyIncludeProtocol(parser, default=True)
    flags.AddCacheKeyIncludeHost(parser, default=True)
    flags.AddCacheKeyIncludeQueryString(parser, default=True)
    flags.AddCacheKeyQueryStringList(parser)
    flags.AddCacheKeyExtendedCachingArgs(parser)
    AddIapFlag(parser)
    parser.display_info.AddCacheUpdater(flags.BackendServicesCompleter)
    signed_url_flags.AddSignedUrlCacheMaxAge(parser, required=False)

    if support_subsetting:
      flags.AddSubsettingPolicy(parser)
      if support_subsetting_subset_size:
        flags.AddSubsettingSubsetSize(parser)

    if support_failover:
      flags.AddConnectionDrainOnFailover(parser, default=None)
      flags.AddDropTrafficIfUnhealthy(parser, default=None)
      flags.AddFailoverRatio(parser)

    flags.AddEnableLogging(parser)
    flags.AddLoggingSampleRate(parser)
    flags.AddLoggingOptional(parser)
    flags.AddLoggingOptionalFields(parser)

    if support_multinic:
      flags.AddNetwork(parser)

    flags.AddLocalityLbPolicy(parser)

    cdn_flags.AddCdnPolicyArgs(parser, 'backend service')

    flags.AddConnectionTrackingPolicy(parser)

    flags.AddCompressionMode(parser)

    if support_ip_address_selection_policy:
      flags.AddIpAddressSelectionPolicy(parser)

  def __init__(
      self,
      support_failover,
      support_multinic,
      support_subsetting,
      support_subsetting_subset_size,
      support_advanced_load_balancing,
      support_ip_address_selection_policy,
      release_track,
  ):
    self._support_failover = support_failover
    self._support_multinic = support_multinic
    self._support_subsetting = support_subsetting
    self._support_subsetting_subset_size = support_subsetting_subset_size
    self._support_advanced_load_balancing = support_advanced_load_balancing
    self._support_ip_address_selection_policy = (
        support_ip_address_selection_policy
    )
    self._release_track = release_track

  def _CreateGlobalRequests(self, holder, args, backend_services_ref):
    """Returns a global backend service create request."""

    if args.load_balancing_scheme == 'INTERNAL':
      raise exceptions.RequiredArgumentException(
          '--region', 'Must specify --region for internal load balancer.')
    if (
        self._support_failover and
        backend_services_utils.HasFailoverPolicyArgs(args)
        ):
      raise exceptions.InvalidArgumentException(
          '--global',
          'failover policy parameters are only for regional passthrough '
          'Network Load Balancers.')
    backend_service = self._CreateBackendService(holder, args,
                                                 backend_services_ref)

    client = holder.client
    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = (
          client.messages.ConnectionDraining(
              drainingTimeoutSec=args.connection_draining_timeout))

    if args.enable_cdn is not None:
      backend_service.enableCDN = args.enable_cdn

    backend_services_utils.ApplyCdnPolicyArgs(
        client,
        args,
        backend_service,
        is_update=False,
        apply_signed_url_cache_max_age=True)

    if (self._support_advanced_load_balancing and
        args.service_lb_policy is not None):
      backend_service.serviceLbPolicy = reference_utils.BuildServiceLbPolicyUrl(
          project_name=backend_services_ref.project,
          location='global',
          policy_name=args.service_lb_policy,
          release_track=self._release_track,
      )
    if args.service_bindings is not None:
      backend_service.serviceBindings = [
          reference_utils.BuildServiceBindingUrl(backend_services_ref.project,
                                                 'global', binding_name)
          for binding_name in args.service_bindings
      ]
    if args.compression_mode is not None:
      backend_service.compressionMode = (
          client.messages.BackendService.CompressionModeValueValuesEnum(
              args.compression_mode))
    if self._support_subsetting:
      backend_services_utils.ApplySubsettingArgs(
          client, args, backend_service, self._support_subsetting_subset_size)
    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          client.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))
    if args.affinity_cookie_ttl is not None:
      backend_service.affinityCookieTtlSec = args.affinity_cookie_ttl
    if args.custom_request_header is not None:
      backend_service.customRequestHeaders = args.custom_request_header
    if args.custom_response_header is not None:
      backend_service.customResponseHeaders = args.custom_response_header
    if (backend_service.cdnPolicy is not None and
        backend_service.cdnPolicy.cacheMode and args.enable_cdn is not False):  # pylint: disable=g-bool-id-comparison
      backend_service.enableCDN = True

    if args.locality_lb_policy is not None:
      backend_service.localityLbPolicy = (
          client.messages.BackendService.LocalityLbPolicyValueValuesEnum(
              args.locality_lb_policy))

    self._ApplyIapArgs(client.messages, args.iap, backend_service)

    if args.load_balancing_scheme != 'EXTERNAL':
      backend_service.loadBalancingScheme = (
          client.messages.BackendService.LoadBalancingSchemeValueValuesEnum(
              args.load_balancing_scheme))

    backend_services_utils.ApplyLogConfigArgs(
        client.messages,
        args,
        backend_service,
    )

    if self._support_ip_address_selection_policy:
      backend_services_utils.ApplyIpAddressSelectionPolicyArgs(
          client, args, backend_service
      )

    request = client.messages.ComputeBackendServicesInsertRequest(
        backendService=backend_service, project=backend_services_ref.project
    )

    return [(client.apitools_client.backendServices, 'Insert', request)]

  def _CreateRegionalRequests(self, holder, args, backend_services_ref):
    """Returns a regional backend service create request."""

    if (
        not args.cache_key_include_host
        or not args.cache_key_include_protocol
        or not args.cache_key_include_query_string
        or args.cache_key_query_string_blacklist is not None
        or args.cache_key_query_string_whitelist is not None
    ):
      raise compute_exceptions.ArgumentError(
          'Custom cache key flags cannot be used for regional requests.'
      )

    if (
        self._support_multinic
        and args.IsSpecified('network')
        and args.load_balancing_scheme != 'INTERNAL'
    ):
      raise exceptions.InvalidArgumentException(
          '--network', 'can only specify network for INTERNAL backend service.'
      )

    backend_service = self._CreateRegionBackendService(
        holder, args, backend_services_ref
    )
    client = holder.client

    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = client.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout
      )
    if args.custom_request_header is not None:
      backend_service.customRequestHeaders = args.custom_request_header
    if args.custom_response_header is not None:
      backend_service.customResponseHeaders = args.custom_response_header
    backend_services_utils.ApplyFailoverPolicyArgs(
        client.messages, args, backend_service, self._support_failover
    )
    if (
        self._support_advanced_load_balancing
        and args.service_lb_policy is not None
    ):
      raise compute_exceptions.ArgumentError(
          '--service-lb-policy flag cannot be used for regional backend'
          ' service.'
      )

    if args.service_bindings is not None:
      region = backend_services_ref.region
      backend_service.serviceBindings = [
          reference_utils.BuildServiceBindingUrl(backend_services_ref.project,
                                                 region, binding_name)
          for binding_name in args.service_bindings
      ]

    if self._support_subsetting:
      backend_services_utils.ApplySubsettingArgs(
          client, args, backend_service, self._support_subsetting_subset_size)

    backend_services_utils.ApplyConnectionTrackingPolicyArgs(
        client, args, backend_service)

    self._ApplyIapArgs(client.messages, args.iap, backend_service)

    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          client.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))

    if args.port_name is not None:
      backend_service.portName = args.port_name

    if self._support_multinic and args.IsSpecified('network'):
      backend_service.network = flags.NETWORK_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()

    if args.locality_lb_policy is not None:
      backend_service.localityLbPolicy = (
          client.messages.BackendService.LocalityLbPolicyValueValuesEnum(
              args.locality_lb_policy))

    backend_services_utils.ApplyLogConfigArgs(
        client.messages,
        args,
        backend_service,
    )

    if self._support_ip_address_selection_policy:
      backend_services_utils.ApplyIpAddressSelectionPolicyArgs(
          client, args, backend_service
      )

    request = client.messages.ComputeRegionBackendServicesInsertRequest(
        backendService=backend_service,
        region=backend_services_ref.region,
        project=backend_services_ref.project)

    return [(client.apitools_client.regionBackendServices, 'Insert', request)]

  def _CreateBackendService(self, holder, args, backend_services_ref):
    health_checks = flags.GetHealthCheckUris(args, self, holder.resources)
    enable_cdn = True if args.enable_cdn else None

    return holder.client.messages.BackendService(
        description=args.description,
        name=backend_services_ref.Name(),
        healthChecks=health_checks,
        portName=_ResolvePortName(args),
        protocol=_ResolveProtocol(holder.client.messages, args),
        timeoutSec=args.timeout,
        enableCDN=enable_cdn)

  def _CreateRegionBackendService(self, holder, args, backend_services_ref):
    """Creates a regional backend service."""

    health_checks = flags.GetHealthCheckUris(args, self, holder.resources)
    messages = holder.client.messages

    return messages.BackendService(
        description=args.description,
        name=backend_services_ref.Name(),
        healthChecks=health_checks,
        loadBalancingScheme=(
            messages.BackendService.LoadBalancingSchemeValueValuesEnum(
                args.load_balancing_scheme)),
        protocol=_ResolveProtocol(messages, args, default='TCP'),
        timeoutSec=args.timeout)

  def _ApplyIapArgs(self, messages, iap_arg, backend_service):
    if iap_arg is not None:
      backend_service.iap = backend_services_utils.GetIAP(iap_arg, messages)
      if backend_service.iap.enabled:
        log.warning(backend_services_utils.IapBestPracticesNotice())
      if (backend_service.iap.enabled and backend_service.protocol
          is not messages.BackendService.ProtocolValueValuesEnum.HTTPS):
        log.warning(backend_services_utils.IapHttpWarning())

  def Run(self, args, holder):
    """Issues request necessary to create Backend Service."""

    client = holder.client
    ref = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    if ref.Collection() == 'compute.backendServices':
      requests = self._CreateGlobalRequests(holder, args, ref)
    elif ref.Collection() == 'compute.regionBackendServices':
      requests = self._CreateRegionalRequests(holder, args, ref)

    return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a backend service.

  *{command}* creates a backend service for a Google Cloud load balancer or
  Traffic Director. A backend service defines how to distribute traffic to
  backends. Depending on the load balancing scheme of the backend service,
  backends can be instance groups (managed or unmanaged), zonal network endpoint
  groups (zonal NEGs), serverless NEGs, or an internet NEG. For more
  information, see the [backend services
  overview](https://cloud.google.com/load-balancing/docs/backend-service).

  After you create a backend service, you add backends by using `gcloud
  compute backend-services add-backend` or `gcloud compute backend-services
  edit`.

  """

  _support_failover = True
  _support_multinic = True
  _support_client_only = True
  _support_unspecified_protocol = True
  _support_subsetting = True
  _support_subsetting_subset_size = False
  _support_advanced_load_balancing = False
  _support_ip_address_selection_policy = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_failover=cls._support_failover,
        support_multinic=cls._support_multinic,
        support_client_only=cls._support_client_only,
        support_unspecified_protocol=cls._support_unspecified_protocol,
        support_subsetting=cls._support_subsetting,
        support_subsetting_subset_size=cls._support_subsetting_subset_size,
        support_advanced_load_balancing=cls._support_advanced_load_balancing,
        support_ip_address_selection_policy=(
            cls._support_ip_address_selection_policy
        ),
    )

  def Run(self, args):
    """Issues request necessary to create Backend Service."""

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return CreateHelper(
        support_failover=self._support_failover,
        support_multinic=self._support_multinic,
        support_subsetting=self._support_subsetting,
        support_subsetting_subset_size=self._support_subsetting_subset_size,
        support_advanced_load_balancing=self._support_advanced_load_balancing,
        support_ip_address_selection_policy=(
            self._support_ip_address_selection_policy
        ),
        release_track=self.ReleaseTrack(),
    ).Run(args, holder)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create a backend service.

  *{command}* creates a backend service. A backend service defines how Cloud
  Load Balancing distributes traffic. The backend service configuration contains
  a set of values, such as the protocol used to connect to backends, various
  distribution and session settings, health checks, and timeouts. These settings
  provide fine-grained control over how your load balancer behaves. Most of the
  settings have default values that allow for easy configuration if you need to
  get started quickly.

  After you create a backend service, you add backends by using `gcloud
  compute backend-services add-backend`.

  For more information about the available settings, see
  https://cloud.google.com/load-balancing/docs/backend-service.
  """
  _support_multinic = True
  _support_client_only = True
  _support_unspecified_protocol = True
  _support_subsetting = True
  _support_subsetting_subset_size = True
  _support_advanced_load_balancing = True
  _support_ip_address_selection_policy = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a backend service.

  *{command}* creates a backend service. A backend service defines how Cloud
  Load Balancing distributes traffic. The backend service configuration contains
  a set of values, such as the protocol used to connect to backends, various
  distribution and session settings, health checks, and timeouts. These settings
  provide fine-grained control over how your load balancer behaves. Most of the
  settings have default values that allow for easy configuration if you need to
  get started quickly.

  After you create a backend service, you add backends by using `gcloud
  compute backend-services add-backend`.

  For more information about the available settings, see
  https://cloud.google.com/load-balancing/docs/backend-service.
  """
  _support_client_only = True
  _support_unspecified_protocol = True
  _support_subsetting = True
  _support_subsetting_subset_size = True
  _support_advanced_load_balancing = True
  _support_ip_address_selection_policy = True
