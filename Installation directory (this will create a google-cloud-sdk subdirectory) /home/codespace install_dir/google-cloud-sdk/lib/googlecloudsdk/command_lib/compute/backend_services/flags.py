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
"""Flags and helpers for the compute backend-services commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.network_services import completers as network_services_completers
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import arg_utils

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      backends[].group.scoped_suffixes().list():label=BACKENDS,
      protocol
    )"""

DEFAULT_BETA_LIST_FORMAT = """\
    table(
      name,
      backends[].group.scoped_suffixes().list():label=BACKENDS,
      protocol,
      loadBalancingScheme,
      healthChecks.map().basename().list()
    )"""


class RegionalBackendServicesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalBackendServicesCompleter, self).__init__(
        collection='compute.regionBackendServices',
        list_command=('compute backend-services list '
                      '--filter=region:* --uri'),
        **kwargs)


class GlobalBackendServicesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalBackendServicesCompleter, self).__init__(
        collection='compute.backendServices',
        list_command=('compute backend-services list --global --uri'),
        **kwargs)


class BackendServicesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(BackendServicesCompleter, self).__init__(
        completers=[
            RegionalBackendServicesCompleter, GlobalBackendServicesCompleter
        ],
        **kwargs)


ZONAL_INSTANCE_GROUP_ARG = compute_flags.ResourceArgument(
    name='--instance-group',
    resource_name='instance group',
    completer=compute_completers.InstanceGroupsCompleter,
    zonal_collection='compute.instanceGroups',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)

MULTISCOPE_INSTANCE_GROUP_ARG = compute_flags.ResourceArgument(
    name='--instance-group',
    resource_name='instance group',
    completer=compute_completers.InstanceGroupsCompleter,
    zonal_collection='compute.instanceGroups',
    regional_collection='compute.regionInstanceGroups',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)

GLOBAL_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=GlobalBackendServicesCompleter,
    global_collection='compute.backendServices')

GLOBAL_MULTI_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=BackendServicesCompleter,
    plural=True,
    global_collection='compute.backendServices')

GLOBAL_REGIONAL_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=BackendServicesCompleter,
    regional_collection='compute.regionBackendServices',
    global_collection='compute.backendServices')

GLOBAL_REGIONAL_BACKEND_SERVICE_NOT_REQUIRED_ARG = (
    compute_flags.ResourceArgument(
        name='backend_service_name',
        required=False,
        resource_name='backend service',
        completer=BackendServicesCompleter,
        regional_collection='compute.regionBackendServices',
        global_collection='compute.backendServices'
    )
)

GLOBAL_REGIONAL_MULTI_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=BackendServicesCompleter,
    plural=True,
    regional_collection='compute.regionBackendServices',
    global_collection='compute.backendServices')

NETWORK_ARG = compute_flags.ResourceArgument(
    name='--network',
    required=False,
    resource_name='network',
    global_collection='compute.networks',
    short_help='Network that this backend service applies to.',
    detailed_help="""\
        Network that this backend service applies to. It can only be set if
        the load-balancing-scheme is INTERNAL.
        """)


def GetNetworkEndpointGroupArg(support_global_neg=False,
                               support_region_neg=False):
  return compute_flags.ResourceArgument(
      name='--network-endpoint-group',
      resource_name='network endpoint group',
      zonal_collection='compute.networkEndpointGroups',
      global_collection='compute.globalNetworkEndpointGroups'
      if support_global_neg else None,
      regional_collection='compute.regionNetworkEndpointGroups'
      if support_region_neg else None,
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION
      if support_region_neg else None)


def BackendServiceArgumentForUrlMap(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--default-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      regional_collection='compute.regionBackendServices',
      short_help=(
          'A backend service that will be used for requests for which this '
          'URL map has no mappings.'),
      region_explanation=('If not specified it will be set to the '
                          'region of the URL map.'))


def BackendServiceArgumentForUrlMapPathMatcher(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--default-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      short_help=(
          'A backend service that will be used for requests that the path '
          'matcher cannot match.'))


def BackendServiceArgumentForTargetSslProxy(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--backend-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      short_help=('.'),
      detailed_help="""\
        A backend service that will be used for connections to the target SSL
        proxy.
        """)


def BackendServiceArgumentForTargetTcpProxy(required=True,
                                            allow_regional=False):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--backend-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      regional_collection='compute.regionBackendServices'
      if allow_regional else None,
      region_explanation=('If not specified it will be set to the '
                          'region of the TCP Proxy.'),
      short_help=('.'),
      detailed_help="""\
        A backend service that will be used for connections to the target TCP
        proxy.
        """)


def AddLoadBalancingScheme(parser):
  parser.add_argument(
      '--load-balancing-scheme',
      choices=[
          'INTERNAL', 'EXTERNAL', 'INTERNAL_SELF_MANAGED', 'EXTERNAL_MANAGED',
          'INTERNAL_MANAGED'
      ],
      type=lambda x: x.replace('-', '_').upper(),
      default='EXTERNAL',
      help="""\
      Specifies the load balancer type. Choose EXTERNAL for the classic
      Application Load Balancers, the external passthrough Network Load
      Balancers, and the global external proxy Network Load Balancers.
      Choose EXTERNAL_MANAGED for the Envoy-based global and regional external
      Application Load Balancers, and the regional external proxy Network Load
      Balancers. Choose INTERNAL for the internal
      passthrough Network Load Balancers. Choose INTERNAL_MANAGED for
      Envoy-based internal load balancers such as the internal Application
      Load Balancers and the internal proxy Network Load Balancers. Choose
      INTERNAL_SELF_MANAGED for
      Traffic Director. For more information, refer to this guide:
      https://cloud.google.com/load-balancing/docs/choosing-load-balancer
      """)


def AddSubsettingPolicy(parser):
  parser.add_argument(
      '--subsetting-policy',
      choices=['NONE', 'CONSISTENT_HASH_SUBSETTING'],
      type=lambda x: x.replace('-', '_').upper(),
      default='NONE',
      help="""\
      Specifies the algorithm used for subsetting.
      Default value is NONE which implies that subsetting is disabled.
      For Layer 4 Internal Load Balancing, if subsetting is enabled,
      only the algorithm CONSISTENT_HASH_SUBSETTING can be specified.
      """)


def AddIpAddressSelectionPolicy(parser):
  parser.add_argument(
      '--ip-address-selection-policy',
      choices=['IPV4_ONLY', 'PREFER_IPV6', 'IPV6_ONLY'],
      type=lambda x: x.replace('-', '_').upper(),
      help="""\
      Specifies a preference for traffic sent from the proxy to the backend (or
      from the client to the backend for proxyless gRPC).

      Can only be set if load balancing scheme is INTERNAL_SELF_MANAGED,
      INTERNAL_MANAGED or EXTERNAL_MANAGED.

      The possible values are:

       IPV4_ONLY
         Only send IPv4 traffic to the backends of the backend service,
         regardless of traffic from the client to the proxy. Only IPv4
         health checks are used to check the health of the backends.

       PREFER_IPV6
         Prioritize the connection to the endpoint's IPv6 address over its IPv4
         address (provided there is a healthy IPv6 address).

       IPV6_ONLY
         Only send IPv6 traffic to the backends of the backend service,
         regardless of traffic from the client to the proxy. Only IPv6
         health checks are used to check the health of the backends.
      """,
  )


def AddLocalityLbPolicy(parser):
  """Add flags related to lb algorithm used within the scope of the locality.

  Args:
    parser: The parser that parses args from user input.
  """
  parser.add_argument(
      '--locality-lb-policy',
      choices=[
          'INVALID_LB_POLICY', 'ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH',
          'RANDOM', 'ORIGINAL_DESTINATION', 'MAGLEV', 'WEIGHTED_MAGLEV'
      ],
      type=lambda x: x.replace('-', '_').upper(),
      default=None,
      help="""\
      The load balancing algorithm used within the scope of the locality.
      """)


def AddConnectionTrackingPolicy(parser):
  """Add flags related to connection tracking policy.

  Args:
    parser: The parser that parses args from user input.
  """
  parser.add_argument(
      '--connection-persistence-on-unhealthy-backends',
      choices=['DEFAULT_FOR_PROTOCOL', 'NEVER_PERSIST', 'ALWAYS_PERSIST'],
      type=lambda x: x.replace('-', '_').upper(),
      default=None,
      help="""\
      Specifies connection persistence when backends are unhealthy.
      The default value is DEFAULT_FOR_PROTOCOL.
      """)
  parser.add_argument(
      '--tracking-mode',
      choices=['PER_CONNECTION', 'PER_SESSION'],
      type=lambda x: x.replace('-', '_').upper(),
      default=None,
      help="""\
      Specifies the connection key used for connection tracking.
      The default value is PER_CONNECTION. Applicable only for backend
      service-based external and internal passthrough Network Load
      Balancers as part of a connection tracking policy.
      For details, see: [Connection tracking mode for
      internal passthrough Network Load Balancers
      balancing](https://cloud.google.com/load-balancing/docs/internal#tracking-mode)
      and [Connection tracking mode for external passthrough Network Load
      Balancers](https://cloud.google.com/load-balancing/docs/network/networklb-backend-service#tracking-mode).
      """)
  parser.add_argument(
      '--idle-timeout-sec',
      type=arg_parsers.Duration(),
      default=None,
      help="""\
      Specifies how long to keep a connection tracking table entry while there
      is no matching traffic (in seconds). Applicable only for backend
      service-based external and internal passthrough Network Load
      Balancers as part of a connection tracking policy.
      """)
  parser.add_argument(
      '--enable-strong-affinity',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      Enable or disable strong session affinity.
      This is only available for loadbalancingScheme EXTERNAL.
      """)


def AddSubsettingSubsetSize(parser):
  parser.add_argument(
      '--subsetting-subset-size',
      type=int,
      help="""\
      Number of backends per backend group assigned to each proxy instance
      or each service mesh client. Can only be set if subsetting policy is
      CONSISTENT_HASH_SUBSETTING and load balancing scheme is either
      INTERNAL_MANAGED or INTERNAL_SELF_MANAGED.
      """)


def AddConnectionDrainingTimeout(parser):
  parser.add_argument(
      '--connection-draining-timeout',
      type=arg_parsers.Duration(upper_bound='1h'),
      help="""\
      Connection draining timeout to be used during removal of VMs from
      instance groups. This guarantees that for the specified time all existing
      connections to a VM will remain untouched, but no new connections will be
      accepted. Set timeout to zero to disable connection draining. Enable
      feature by specifying a timeout of up to one hour.
      If the flag is omitted API default value (0s) will be used.
      See $ gcloud topic datetimes for information on duration formats.
      """)


def AddCustomRequestHeaders(parser, remove_all_flag=False, default=None):
  """Adds custom request header flag to the argparse."""
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--custom-request-header',
      action='append',
      help="""\
      Specifies a HTTP Header to be added by your load balancer.
      This flag can be repeated to specify multiple headers.
      For example:

        $ {command} NAME \
            --custom-request-header "header-name: value" \
            --custom-request-header "another-header:"
      """)
  if remove_all_flag:
    group.add_argument(
        '--no-custom-request-headers',
        action='store_true',
        default=default,
        help="""\
        Remove all custom request headers for the backend service.
        """)


def AddEnableCdn(parser):
  parser.add_argument(
      '--enable-cdn',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      Enable or disable Cloud CDN for the backend service. Only available for
      backend services with --load-balancing-scheme=EXTERNAL that use a
      --protocol of HTTP, HTTPS, or HTTP2. Cloud CDN caches HTTP responses at
      the edge of Google's network. Cloud CDN is disabled by default.
      """)


def AddCacheKeyIncludeProtocol(parser, default):
  """Adds cache key include/exclude protocol flag to the argparse."""
  parser.add_argument(
      '--cache-key-include-protocol',
      action='store_true',
      default=default,
      help="""\
      Enable including protocol in cache key. If enabled, http and https
      requests will be cached separately. Can only be applied for global
      resources.""")


def AddCacheKeyIncludeHost(parser, default):
  """Adds cache key include/exclude host flag to the argparse."""
  parser.add_argument(
      '--cache-key-include-host',
      action='store_true',
      default=default,
      help="""\
      Enable including host in cache key. If enabled, requests to different
      hosts will be cached separately. Can only be applied for global resources.
      """)


def AddCacheKeyIncludeQueryString(parser, default):
  """Adds cache key include/exclude query string flag to the argparse."""
  update_command = default is None
  if update_command:
    update_command_help = """\
        Enable including query string in cache key. If enabled, the query string
        parameters will be included according to
        --cache-key-query-string-whitelist and
        --cache-key-query-string-blacklist. If disabled, the entire query string
        will be excluded. Use "--cache-key-query-string-blacklist=" (sets the
        blacklist to the empty list) to include the entire query string. Can
        only be applied for global resources.
        """
  else:  # create command
    update_command_help = """\
        Enable including query string in cache key. If enabled, the query string
        parameters will be included according to
        --cache-key-query-string-whitelist and
        --cache-key-query-string-blacklist. If neither is set, the entire query
        string will be included. If disabled, then the entire query string will
        be excluded. Can only be applied for global resources.
        """
  parser.add_argument(
      '--cache-key-include-query-string',
      action='store_true',
      default=default,
      help=update_command_help)


def AddCacheKeyQueryStringList(parser):
  """Adds cache key include/exclude query string flags to the argparse."""
  cache_key_query_string_list = parser.add_mutually_exclusive_group()
  cache_key_query_string_list.add_argument(
      '--cache-key-query-string-whitelist',
      type=arg_parsers.ArgList(min_length=1),
      metavar='QUERY_STRING',
      default=None,
      help="""\
      Specifies a comma separated list of query string parameters to include
      in cache keys. All other parameters will be excluded. Either specify
      --cache-key-query-string-whitelist or --cache-key-query-string-blacklist,
      not both. '&' and '=' will be percent encoded and not treated as
      delimiters. Can only be applied for global resources.
      """)
  cache_key_query_string_list.add_argument(
      '--cache-key-query-string-blacklist',
      type=arg_parsers.ArgList(),
      metavar='QUERY_STRING',
      default=None,
      help="""\
      Specifies a comma separated list of query string parameters to exclude
      in cache keys. All other parameters will be included. Either specify
      --cache-key-query-string-whitelist or --cache-key-query-string-blacklist,
      not both. '&' and '=' will be percent encoded and not treated as
      delimiters. Can only be applied for global resources.
      """)


def AddCacheKeyExtendedCachingArgs(parser):
  """Adds cache key includeHttpHeader and includeNamedCookie flags to the argparse."""
  parser.add_argument(
      '--cache-key-include-http-header',
      type=arg_parsers.ArgList(),
      metavar='HEADER_FIELD_NAME',
      help="""\
      Specifies a comma-separated list of HTTP headers, by field name, to
      include in cache keys. Only the request URL is included in the cache
      key by default.
      """)

  parser.add_argument(
      '--cache-key-include-named-cookie',
      type=arg_parsers.ArgList(),
      metavar='NAMED_COOKIE',
      help="""\
      Specifies a comma-separated list of HTTP cookie names to include in cache
      keys. The name=value pair are used in the cache key Cloud CDN
      generates. Cookies are not included in cache keys by default.
      """)


def HealthCheckArgument(required=False):
  return compute_flags.ResourceArgument(
      resource_name='health check',
      name='--health-checks',
      completer=compute_completers.HealthChecksCompleter,
      plural=True,
      required=required,
      global_collection='compute.healthChecks',
      regional_collection='compute.regionHealthChecks',
      short_help="""\
      Specifies a list of health check objects for checking the health of
      the backend service. Currently at most one health check can be specified.
      Health checks need not be for the same protocol as that of the backend
      service.
      """,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def HttpHealthCheckArgument(required=False):
  return compute_flags.ResourceArgument(
      resource_name='http health check',
      name='--http-health-checks',
      completer=compute_completers.HttpHealthChecksCompleter,
      plural=True,
      required=required,
      global_collection='compute.httpHealthChecks',
      short_help="""\
      Specifies a list of legacy HTTP health check objects for checking the
      health of the backend service.

      Legacy health checks are not recommended for backend services. It is
      possible to use a legacy health check on a backend service for an
      Application Load Balancer if that backend service uses instance groups.
      For more information, refer to this guide:
      https://cloud.google.com/load-balancing/docs/health-check-concepts#lb_guide.
      """)


def HttpsHealthCheckArgument(required=False):
  return compute_flags.ResourceArgument(
      resource_name='https health check',
      name='--https-health-checks',
      completer=compute_completers.HttpsHealthChecksCompleter,
      plural=True,
      required=required,
      global_collection='compute.httpsHealthChecks',
      short_help="""\
      Specifies a list of legacy HTTPS health check objects for checking the
      health of the backend service.

      Legacy health checks are not recommended for backend services. It is
      possible to use a legacy health check on a backend service for an
      Application Load Balancer  if that backend service uses instance groups.
      For more information, refer to this guide:
      https://cloud.google.com/load-balancing/docs/health-check-concepts#lb_guide.
      """)


def AddNoHealthChecks(parser, default=None):
  """Adds the no health checks argument to the argparse."""
  parser.add_argument(
      '--no-health-checks',
      action='store_true',
      default=default,
      help="""\
      Removes all health checks for the backend service if the backend service
      has no backends attached.
      """)


def GetHealthCheckUris(args, resource_resolver, resource_parser):
  """Returns health check URIs from arguments."""
  health_check_refs = []

  if args.http_health_checks:
    health_check_refs.extend(
        resource_resolver.HTTP_HEALTH_CHECK_ARG.ResolveAsResource(
            args, resource_parser))

  if getattr(args, 'https_health_checks', None):
    health_check_refs.extend(
        resource_resolver.HTTPS_HEALTH_CHECK_ARG.ResolveAsResource(
            args, resource_parser))

  if getattr(args, 'health_checks', None):
    if health_check_refs:
      raise compute_exceptions.ArgumentError(
          'Mixing --health-checks with --http-health-checks or with '
          '--https-health-checks is not supported.')
    else:
      health_check_refs.extend(
          resource_resolver.HEALTH_CHECK_ARG.ResolveAsResource(
              args,
              resource_parser,
              default_scope=compute_scope.ScopeEnum.GLOBAL))

  if health_check_refs and getattr(args, 'no_health_checks', None):
    raise compute_exceptions.ArgumentError(
        'Combining --health-checks, --http-health-checks, or '
        '--https-health-checks with --no-health-checks is not supported.')

  return [health_check_ref.SelfLink() for health_check_ref in health_check_refs]


SERVICE_LB_POLICY_HELP = """\
Service load balancing policy to be applied to this backend service.
Can only be set if load balancing scheme is EXTERNAL_MANAGED,
INTERNAL_MANAGED, or INTERNAL_SELF_MANAGED. Only available for global backend
services.
"""


def AddServiceLoadBalancingPolicy(parser, required=False, is_update=False):
  """Add support for --service-lb-policy flag."""
  group = parser.add_mutually_exclusive_group() if is_update else parser
  group.add_argument(
      '--service-lb-policy',
      metavar='SERVICE_LOAD_BALANCING_POLICY',
      required=required,
      # TODO(b/199261738): enable when gcloud list command for serviceLbPolicy
      # is available
      # completer=(
      #    network_services_completers.ServiceLoadBalancingPoliciesCompleter),
      help=SERVICE_LB_POLICY_HELP)
  if is_update:
    group.add_argument(
        '--no-service-lb-policy',
        required=False,
        action='store_true',
        default=None,
        help='No service load balancing policies should be attached '
        'to the backend service.')


SERVICE_BINDINGS_HELP = """\
List of service bindings to be attached to this backend service.
Can only be set if load balancing scheme is INTERNAL_SELF_MANAGED.
If set, lists of backends and health checks must be both empty.
"""


def AddServiceBindings(parser, required=False, is_update=False, help_text=None):
  """Add support for --service_bindings flag."""
  group = parser.add_mutually_exclusive_group() if is_update else parser
  group.add_argument(
      '--service-bindings',
      metavar='SERVICE_BINDING',
      required=required,
      type=arg_parsers.ArgList(min_length=1),
      completer=network_services_completers.ServiceBindingsCompleter,
      help=help_text if help_text is not None else SERVICE_BINDINGS_HELP)
  if is_update:
    group.add_argument(
        '--no-service-bindings',
        required=False,
        action='store_true',
        default=None,
        help='No service bindings should be attached to the backend service.')


def AddCompressionMode(parser):
  """Add support for --compression-mode flag."""
  return parser.add_argument(
      '--compression-mode',
      choices=['DISABLED', 'AUTOMATIC'],
      type=arg_utils.ChoiceToEnumName,
      help="""\
      Compress text responses using Brotli or gzip compression, based on
      the client's Accept-Encoding header. Two modes are supported:
      AUTOMATIC (recommended) - automatically uses the best compression based
      on the Accept-Encoding header sent by the client. In most cases, this
      will result in Brotli compression being favored.
      DISABLED - disables compression. Existing compressed responses cached
      by Cloud CDN will not be served to clients.
      """)


def AddIap(parser, help=None):  # pylint: disable=redefined-builtin
  """Add support for --iap flag."""
  # We set this to str, but it's really an ArgDict.  See
  # backend_services_utils.GetIAP for the re-parse and rationale.
  return parser.add_argument(
      '--iap',
      metavar=('disabled|enabled,['
               'oauth2-client-id=OAUTH2-CLIENT-ID,'
               'oauth2-client-secret=OAUTH2-CLIENT-SECRET]'),
      help=help or 'Specifies a list of settings for IAP service.')


def AddSessionAffinity(parser,
                       target_pools=False,
                       hidden=False,
                       support_client_only=False):
  """Adds session affinity flag to the argparse.

  Args:
    parser: An argparse.ArgumentParser instance.
    target_pools: Indicates if the backend pool is target pool.
    hidden: if hidden=True, retains help but does not display it.
    support_client_only: Indicates if CLIENT_IP_NO_DESTINATION is valid choice.
  """
  choices = {
      'CLIENT_IP':
          ("Route requests to instances based on the hash of the client's IP "
           'address.'),
      'NONE':
          'Session affinity is disabled.',
      'CLIENT_IP_PROTO':
          ('Connections from the same client IP with the same IP '
           'protocol will go to the same VM in the pool while that VM remains'
           ' healthy.'),
  }

  if not target_pools:
    choices.update({
        'GENERATED_COOKIE': (
            '(Applicable if `--load-balancing-scheme` is '
            '`INTERNAL_MANAGED`, `INTERNAL_SELF_MANAGED`, `EXTERNAL_MANAGED`, '
            'or `EXTERNAL`) '
            ' If the `--load-balancing-scheme` is `EXTERNAL` or '
            '`EXTERNAL_MANAGED`, routes requests to backend VMs or endpoints '
            ' in a NEG, based on the contents of the `GCLB` cookie set by the '
            ' load balancer. Only applicable when `--protocol` is HTTP, HTTPS, '
            ' or HTTP2. If the `--load-balancing-scheme` is `INTERNAL_MANAGED` '
            ' or `INTERNAL_SELF_MANAGED`, routes requests to backend VMs or '
            ' endpoints in a NEG, based on the contents of the `GCILB` cookie '
            ' set by the proxy. (If no cookie is present, the proxy '
            ' chooses a backend VM or endpoint and sends a `Set-Cookie` '
            ' response for future requests.) If the `--load-balancing-scheme` '
            ' is `INTERNAL_SELF_MANAGED`, routes requests to backend VMs or '
            ' endpoints in a NEG, based on the contents of a cookie set by '
            ' Traffic Director. This session affinity is only valid if the '
            ' load balancing locality policy is either `RING_HASH` or '
            ' `MAGLEV`.'),
        'CLIENT_IP_PROTO':
            ('(Applicable if `--load-balancing-scheme` is `INTERNAL`) '
             'Connections from the same client IP with the same IP '
             'protocol will go to the same backend VM while that VM remains'
             ' healthy.'),
        'CLIENT_IP_PORT_PROTO': (
            '(Applicable if `--load-balancing-scheme` is `INTERNAL`) '
            'Connections from the same client IP with the same IP protocol and '
            'port will go to the same backend VM while that VM remains '
            'healthy.'),
        'HTTP_COOKIE': (
            '(Applicable if `--load-balancing-scheme` is `INTERNAL_MANAGED`, '
            '`EXTERNAL_MANAGED` or `INTERNAL_SELF_MANAGED`) Route requests to '
            ' backend VMs or '
            ' endpoints in a NEG, based on an HTTP cookie named in the '
            ' `HTTP_COOKIE` flag (with the optional `--affinity-cookie-ttl` '
            ' flag). If the client has not provided the cookie, '
            ' the proxy generates the cookie and returns it to the client in a '
            ' `Set-Cookie` header. This session affinity is only valid if the '
            ' load balancing locality policy is either `RING_HASH` or `MAGLEV` '
            ' and the backend service\'s consistent hash specifies the HTTP '
            ' cookie.'),
        'HEADER_FIELD':
            ('(Applicable if `--load-balancing-scheme` is `INTERNAL_MANAGED`, '
             '`EXTERNAL_MANAGED`, or `INTERNAL_SELF_MANAGED`) Route requests '
             ' to backend VMs or '
             ' endpoints in a NEG based on the value of the HTTP header named '
             ' in the `--custom-request-header` flag. This session '
             ' affinity is only valid if the load balancing locality policy '
             ' is either `RING_HASH` or `MAGLEV` and the backend service\'s '
             ' consistent hash specifies the name of the HTTP header.'),
    })
    if support_client_only:
      choices.update({
          'CLIENT_IP_NO_DESTINATION':
              ('Directs a particular client\'s request to the same backend VM '
               'based on a hash created on the client\'s IP address only. This '
               'is used in L4 ILB as Next-Hop scenarios. It differs from the '
               'Client-IP option in that Client-IP uses a hash based on both '
               'client-IP\'s address and destination address.')
      })
  help_str = 'The type of session affinity to use. Supports both TCP and UDP.'
  parser.add_argument(
      '--session-affinity',
      choices=choices,
      # Tri-valued, None => don't include property.
      default='NONE' if target_pools else None,
      type=lambda x: x.upper(),
      hidden=hidden,
      help=help_str)


def AddAffinityCookieTtl(parser, hidden=False):
  """Adds affinity cookie Ttl flag to the argparse."""
  affinity_cookie_ttl_help = """\
      If session-affinity is set to "generated_cookie", this flag sets
      the TTL, in seconds, of the resulting cookie.  A setting of 0
      indicates that the cookie should be transient.
      See $ gcloud topic datetimes for information on duration formats.
      """
  parser.add_argument(
      '--affinity-cookie-ttl',
      type=arg_parsers.Duration(),
      default=None,  # Tri-valued, None => don't include property.
      help=affinity_cookie_ttl_help,
      hidden=hidden,
  )


def AddDescription(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend service.')


def AddTimeout(parser, default='30s'):
  parser.add_argument(
      '--timeout',
      default=default,
      type=arg_parsers.Duration(),
      help="""\
      Applicable to all load balancing products except passthrough Network Load
      Balancers. For internal passthrough Network Load Balancers
      (``load-balancing-scheme'' set to INTERNAL) and
      external passthrough Network Load Balancers (``global'' not set and
      ``load-balancing-scheme'' set to EXTERNAL), ``timeout'' is ignored.

      If the ``protocol'' is HTTP, HTTPS, or HTTP2, ``timeout'' is a
      request/response timeout for HTTP(S) traffic, meaning the amount
      of time that the load balancer waits for a backend to return a
      full response to a request. If WebSockets traffic is supported, the
      ``timeout'' parameter sets the maximum amount of time that a
      WebSocket can be open (idle or not).

      For example, for HTTP, HTTPS, or HTTP2 traffic, specifying a ``timeout''
      of 10s means that backends have 10 seconds to respond to the load
      balancer's requests. The load balancer retries the HTTP GET request one
      time if the backend closes the connection or times out before sending
      response headers to the load balancer. If the backend sends response
      headers or if the request sent to the backend is not an HTTP GET request,
      the load balancer does not retry. If the backend does not reply at all,
      the load balancer returns a 502 Bad Gateway error to the client.

      If the ``protocol'' is SSL or TCP, ``timeout'' is an idle timeout.

      The full range of timeout values allowed is 1 - 2,147,483,647 seconds.
      """)


def AddPortName(parser):
  """Add port-name flag."""
  parser.add_argument(
      '--port-name',
      help="""\
      Backend services for Application Load Balancers and proxy Network
      Load Balancers must reference exactly one named port if using instance
      group backends.

      Each instance group backend exports one or more named ports, which map a
      user-configurable name to a port number. The backend service's named port
      subscribes to one named port on each instance group. The resolved port
      number can differ among instance group backends, based on each instance
      group's named port list.

      When omitted, a backend service subscribes to a named port called http.

      The named port for a backend service is either ignored or cannot be set
      for these load balancing configurations:

      - For any load balancer, if the backends are not instance groups
        (for example, GCE_VM_IP_PORT NEGs).
      - For any type of backend on a backend service for internal or external
        passthrough Network Load Balancers.

      See also
      https://cloud.google.com/load-balancing/docs/backend-service#named_ports.
      """)


def AddProtocol(parser, default='HTTP', support_unspecified_protocol=False):
  """Adds --protocol flag to the argparse.

  Args:
    parser: An argparse.ArgumentParser instance.
    default: The default protocol if this flag is unspecified.
    support_unspecified_protocol: Indicates if UNSPECIFIED is a valid protocol.
  """
  ilb_protocols = ('TCP, UDP, UNSPECIFIED'
                   if support_unspecified_protocol else 'TCP, UDP')
  td_protocols = ('HTTP, HTTPS, HTTP2, GRPC')
  netlb_protocols = ('TCP, UDP, UNSPECIFIED'
                     if support_unspecified_protocol else 'TCP, UDP')
  parser.add_argument(
      '--protocol',
      default=default,
      type=lambda x: x.upper(),
      help="""\
      Protocol for incoming requests.

      If the `load-balancing-scheme` is `INTERNAL` (Internal passthrough
      Network Load Balancer), the protocol must be one of: {0}.

      If the `load-balancing-scheme` is `INTERNAL_SELF_MANAGED` (Traffic
      Director), the protocol must be one of: {1}.

      If the `load-balancing-scheme` is `INTERNAL_MANAGED` (Internal Application
      Load Balancer), the protocol must be one of: HTTP, HTTPS, HTTP2.

      If the `load-balancing-scheme` is `EXTERNAL` and `region` is not set
      (Classic Application Load Balancer and global external proxy Network
      Load Balancer), the protocol must be one of: HTTP, HTTPS, HTTP2, SSL, TCP.

      If the `load-balancing-scheme` is `EXTERNAL` and `region` is set
      (External passthrough Network Load Balancer), the protocol must be one
      of: {2}.

      If the `load-balancing-scheme` is `EXTERNAL_MANAGED` (Envoy based
      Global and regional external Application Load Balancers), the protocol
      must be one of: HTTP, HTTPS, HTTP2.
      """.format(ilb_protocols, td_protocols, netlb_protocols))


def AddConnectionDrainOnFailover(parser, default):
  """Adds the connection drain on failover argument to the argparse."""
  parser.add_argument(
      '--connection-drain-on-failover',
      action='store_true',
      default=default,
      help="""\
      Applicable only for backend service-based external and internal
      passthrough Network Load Balancers as part of a connection tracking
      policy. Only applicable when the backend service protocol is TCP. Not
      applicable to any other load balancer. Enabled by default, this option
      instructs the load balancer to allow established TCP connections to
      persist for up to 300 seconds on instances or endpoints in primary
      backends during failover, and on instances or endpoints in failover
      backends during failback. For details, see: [Connection draining on
      failover and failback for internal passthrough Network Load
      Balancers](https://cloud.google.com/load-balancing/docs/internal/failover-overview#connection_draining)
      and [Connection draining on failover and failback for external passthrough
      Network Load
      Balancers](https://cloud.google.com/load-balancing/docs/network/networklb-failover-overview#connection_draining).
      """)


def AddDropTrafficIfUnhealthy(parser, default):
  """Adds the drop traffic if unhealthy argument to the argparse."""
  parser.add_argument(
      '--drop-traffic-if-unhealthy',
      action='store_true',
      default=default,
      help="""\
      Applicable only for backend service-based external and internal
      passthrough Network Load Balancers as part of a connection tracking
      policy. Not applicable to any other load balancer. This option instructs
      the load balancer to drop packets when all instances or endpoints in
      primary and failover backends do not pass their load balancer health
      checks. For details, see: [Dropping traffic when all backend VMs are
      unhealthy for internal passthrough Network Load
      Balancers](https://cloud.google.com/load-balancing/docs/internal/failover-overview#drop_traffic)
      and [Dropping traffic when all backend VMs are unhealthy for external
      passthrough Network Load
      Balancers](https://cloud.google.com/load-balancing/docs/network/networklb-failover-overview#drop_traffic).
      """)


def AddFailoverRatio(parser):
  """Adds the failover ratio argument to the argparse."""
  parser.add_argument(
      '--failover-ratio',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      Applicable only to backend service-based external passthrough Network load
      balancers and internal passthrough Network load balancers as part of a
      failover policy. Not applicable to any other load balancer. This option
      defines the ratio used to control when failover and failback occur.
      For details, see: [Failover ratio for internal passthrough Network
      Load Balancers](https://cloud.google.com/load-balancing/docs/internal/failover-overview#failover_ratio)
      and [Failover ratio for external passthrough Network Load Balancer
      overview](https://cloud.google.com/load-balancing/docs/network/networklb-failover-overview#failover_ratio).
      """)


def AddEnableLogging(parser):
  """Adds the enable logging argument to the argparse."""
  parser.add_argument(
      '--enable-logging',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      The logging options for the load balancer traffic served by this backend
      service. If logging is enabled, logs will be exported to Cloud Logging.
      Disabled by default. This field cannot be specified for global external
      proxy Network Load Balancers.
      """,
  )


def AddLoggingSampleRate(parser):
  """Adds the logging sample rate argument to the argparse."""
  parser.add_argument(
      '--logging-sample-rate',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      This field can only be specified if logging is enabled for the backend
      service. The value of the field must be a float in the range [0, 1]. This
      configures the sampling rate of requests to the load balancer where 1.0
      means all logged requests are reported and 0.0 means no logged requests
      are reported. The default value is 1.0 when logging is enabled and 0.0
      otherwise.
      """,
  )


def AddLoggingOptional(parser):
  """Adds the logging optional argument to the argparse."""
  parser.add_argument(
      '--logging-optional',
      choices=['EXCLUDE_ALL_OPTIONAL', 'INCLUDE_ALL_OPTIONAL', 'CUSTOM'],
      type=arg_utils.ChoiceToEnumName,
      help="""\
      This field can only be specified if logging is enabled for the backend
      service. Configures whether all, none, or a subset of optional fields
      should be added to the reported logs. Default is EXCLUDE_ALL_OPTIONAL.
      This field can only be specified for internal and external passthrough
      Network Load Balancers.
      """,
  )


def AddLoggingOptionalFields(parser):
  """Adds the logging optional argument to the argparse."""
  parser.add_argument(
      '--logging-optional-fields',
      type=arg_parsers.ArgList(),
      metavar='LOGGING_OPTIONAL_FIELDS',
      help="""\
      This field can only be specified if logging is enabled for the backend
      service and "--logging-optional" was set to CUSTOM. Contains a
      comma-separated list of optional fields you want to include in the logs.
      For example: serverInstance, serverGkeDetails.cluster,
      serverGkeDetails.pod.podNamespace. This can only be specified for
      internal and external passthrough Network Load Balancers.
      """,
  )


def AddInstanceGroupAndNetworkEndpointGroupArgs(parser,
                                                verb,
                                                support_global_neg=False,
                                                support_region_neg=False):
  """Adds instance group and network endpoint group args to the argparse."""
  backend_group = parser.add_group(required=True, mutex=True)
  instance_group = backend_group.add_group('Instance Group')
  neg_group = backend_group.add_group('Network Endpoint Group')
  MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(
      instance_group, operation_type='{} the backend service'.format(verb))
  neg_group_arg = GetNetworkEndpointGroupArg(
      support_global_neg=support_global_neg,
      support_region_neg=support_region_neg)
  neg_group_arg.AddArgument(
      neg_group, operation_type='{} the backend service'.format(verb))


def AddNetwork(parser):
  NETWORK_ARG.AddArgument(parser)
