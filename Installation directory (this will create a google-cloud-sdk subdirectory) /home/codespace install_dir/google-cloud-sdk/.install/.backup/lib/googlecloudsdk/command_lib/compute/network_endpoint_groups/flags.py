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
"""Flags for the `compute network-endpoint-groups` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags


def MakeNetworkEndpointGroupsArg():
  return compute_flags.ResourceArgument(
      resource_name='network endpoint group',
      zonal_collection='compute.networkEndpointGroups',
      global_collection='compute.globalNetworkEndpointGroups',
      regional_collection='compute.regionNetworkEndpointGroups',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
  )


def _JoinWithOr(strings):
  """Joins strings, for example, into a string like 'A or B' or 'A, B, or C'."""
  if not strings:
    return ''
  elif len(strings) == 1:
    return strings[0]
  elif len(strings) == 2:
    return strings[0] + ' or ' + strings[1]
  else:
    return ', '.join(strings[:-1]) + ', or ' + strings[-1]


def _AddNetworkEndpointGroupType(parser, support_neg_type):
  """Adds NEG type argument for creating network endpoint group."""
  if support_neg_type:
    base.ChoiceArgument(
        '--neg-type',
        hidden=True,
        choices=['load-balancing'],
        default='load-balancing',
        help_str='The type of network endpoint group to create.',
    ).AddToParser(parser)


def _AddNetworkEndpointType(parser):
  """Adds endpoint type argument for creating network endpoint groups."""
  endpoint_type_choices = [
      'gce-vm-ip-port',
      'internet-ip-port',
      'internet-fqdn-port',
      'non-gcp-private-ip-port',
      'serverless',
      'gce-vm-ip',
      'private-service-connect',
  ]

  help_text = """\
      Determines the spec of endpoints attached to this group.

      *gce-vm-ip-port*:::
      Endpoint IP address must belong to a VM in Compute Engine
      (either the primary IP or as part of an aliased IP range).
      The `--default-port` must be specified or every network endpoint
      in the network endpoint group must have a port specified.

      *internet-ip-port*:::
      Endpoint IP address must be a publicly routable address. If specified, the
      default port is used. If unspecified, the well-known port for your backend
      protocol is used as the default port (80 for HTTP, 443 for HTTPS).

      *internet-fqdn-port*:::
      Endpoint FQDN must be resolvable to a public IP address via public
      DNS. The default port is used, if specified. If the default
      port is not specified, the well-known port for your backend
      protocol is used as the default port (80 for HTTP, 443 for
      HTTPS).

      After creating a NEG of this type, you can use the `gcloud compute
      network-endpoint-groups update` command with
      the `--add-endpoint` flag. Example:
      `--add-endpoint="fqdn=backend.example.com,port=443"`

      *non-gcp-private-ip-port*:::
      Endpoint IP address must belong to a VM not in Compute
      Engine and must be routable using a Cloud Router over VPN or an
      Interconnect connection. In this case, the NEG must be zonal. The
      `--default-port` must be specified or every network endpoint in
      the network endpoint group must have a port specified.

      *serverless*:::
      The network endpoint is handled by specified serverless
      infrastructure, such as Cloud Run, App Engine, or Cloud Function.
      Default port, network, and subnet are not effective for serverless
      endpoints.

      *private-service-connect*:::
      The network endpoint corresponds to a service outside the VPC, accessed
      via Private Service Connect.

      *gce-vm-ip*:::
      Endpoint must be the IP address of a VM's network interface in
      Compute Engine. Instance reference is required. The IP address is
      optional. If unspecified, the primary NIC address is used.
      A port must not be specified.
  """

  base.ChoiceArgument(
      '--network-endpoint-type',
      hidden=False,
      choices=endpoint_type_choices,
      default='gce-vm-ip-port',
      help_str=help_text,
  ).AddToParser(parser)


def _AddNetwork(parser):
  """Adds network argument for creating network endpoint groups."""
  help_text = """\
      Name of the network in which the NEG is created. `default` project
      network is used if unspecified.
  """
  network_applicable_ne_types = [
      '`gce-vm-ip-port`',
      '`non-gcp-private-ip-port`',
      '`gce-vm-ip`',
      '`private-service-connect`',
      '`internet-ip-port`',
      '`internet-fqdn-port`',
  ]

  help_text += """\

    This is only supported for NEGs with endpoint type {0}.

    For Private Service Connect NEGs, you can optionally specify --network and
    --subnet if --psc-target-service points to a published service. If
    --psc-target-service points to the regional service endpoint of a Google
    API, do not specify --network or --subnet.
  """.format(_JoinWithOr(network_applicable_ne_types))
  parser.add_argument('--network', help=help_text)


def _AddSubnet(parser):
  """Adds subnet argument for creating network endpoint groups."""
  help_text = """\
      Name of the subnet to which all network endpoints belong.

      If not specified, network endpoints may belong to any subnetwork in the
      region where the network endpoint group is created.
  """
  subnet_applicable_types = ['`gce-vm-ip-port`']
  subnet_applicable_types.append('`gce-vm-ip`')
  subnet_applicable_types.append('`private-service-connect`')
  help_text += """\

      This is only supported for NEGs with endpoint type {0}.
      For Private Service Connect NEGs, you can optionally specify --network and
      --subnet if --psc-target-service points to a published service. If
      --psc-target-service points to the regional service endpoint of a Google
      API, do not specify --network or --subnet.
  """.format(_JoinWithOr(subnet_applicable_types))
  parser.add_argument('--subnet', help=help_text)


def _AddDefaultPort(parser):
  """Adds default port argument for creating network endpoint groups."""
  help_text = """\
    The default port to use if the port number is not specified in the network
    endpoint.

    If this flag isn't specified for a NEG with endpoint type `gce-vm-ip-port`
    or `non-gcp-private-ip-port`, then every network endpoint in the network
    endpoint group must have a port specified. For a global NEG with endpoint
    type `internet-ip-port` and `internet-fqdn-port` if the default port is not
    specified, the well-known port for your backend protocol is used (80 for
    HTTP, 443 for HTTPS).

    This flag is not supported for NEGs with endpoint type `serverless`.

    This flag is not supported for NEGs with endpoint type
    `private-service-connect`.
  """

  parser.add_argument('--default-port', type=int, help=help_text)


def _AddServerlessRoutingInfo(parser, support_serverless_deployment=False):
  """Adds serverless routing info arguments for network endpoint groups."""
  serverless_group_help = """\
      The serverless routing configurations are only valid when endpoint type
      of the network endpoint group is `serverless`.
  """
  serverless_group = parser.add_group(help=serverless_group_help, mutex=True)

  cloud_run_group_help = """\
      Configuration for a Cloud Run network endpoint group. Cloud Run service
      must be provided explicitly or in the URL mask. Cloud Run tag is optional,
      and may be provided explicitly or in the URL mask.
  """
  cloud_run_group = serverless_group.add_group(help=cloud_run_group_help)
  cloud_run_service_help = """\
      Cloud Run service name to add to the Serverless network endpoint groups
      (NEG). The service must be in the same project and the same region as the
      Serverless NEG.
  """
  cloud_run_group.add_argument(
      '--cloud-run-service', help=cloud_run_service_help
  )
  cloud_run_tag_help = """\
      Cloud Run tag represents the "named revision" to provide additional
      fine-grained traffic routing configuration.
  """
  cloud_run_group.add_argument('--cloud-run-tag', help=cloud_run_tag_help)
  cloud_run_url_mask_help = """\
      A template to parse service and tag fields from a request URL. URL mask
      allows for routing to multiple Run services without having to create
      multiple network endpoint groups and backend services.
  """
  cloud_run_group.add_argument(
      '--cloud-run-url-mask', help=cloud_run_url_mask_help
  )

  app_engine_group_help = """\
      Configuration for an App Engine network endpoint group. Both App Engine
      service and version are optional, and may be provided explicitly or in the
      URL mask. The `app-engine-app` flag is only used for default routing. The
      App Engine app must be in the same project as the Serverless network
      endpoint groups (NEG).
  """
  app_engine_group = serverless_group.add_group(help=app_engine_group_help)
  app_engine_group.add_argument(
      '--app-engine-app',
      action=arg_parsers.StoreTrueFalseAction,
      help='If set, the default routing is used.',
  )
  app_engine_group.add_argument(
      '--app-engine-service',
      help='Optional serving service to add to the Serverless NEG.',
  )
  app_engine_group.add_argument(
      '--app-engine-version',
      help='Optional serving version to add to the Serverless NEG.',
  )
  app_engine_url_mask_help = """\
      A template to parse service and version fields from a request URL. URL
      mask allows for routing to multiple App Engine services without having
      to create multiple network endpoint groups and backend services.
  """
  app_engine_group.add_argument(
      '--app-engine-url-mask', help=app_engine_url_mask_help
  )

  cloud_function_group_help = """\
      Configuration for a Cloud Function network endpoint group. Cloud Function
      name must be provided explicitly or in the URL mask.
  """
  cloud_function_group = serverless_group.add_group(
      help=cloud_function_group_help
  )
  cloud_function_name_help = """\
      Cloud Function name to add to the Serverless NEG. The function must be in
      the same project and the same region as the Serverless network endpoint
      groups (NEG).
  """
  cloud_function_group.add_argument(
      '--cloud-function-name', help=cloud_function_name_help
  )
  cloud_function_url_mask_help = """\
      A template to parse function field from a request URL. URL mask allows
      for routing to multiple Cloud Functions without having to create multiple
      network endpoint groups and backend services.
  """
  cloud_function_group.add_argument(
      '--cloud-function-url-mask', help=cloud_function_url_mask_help
  )

  if support_serverless_deployment:
    serverless_deployment_group_help = """\
        Configuration for a Serverless network endpoint group.
        Serverless NEGs support all serverless backends and are the only way to
        setup a network endpoint group for Cloud API Gateways.

        To create a serverless NEG with a Cloud Run, Cloud Functions or App
        Engine endpoint, you can either use the previously-listed Cloud Run,
        Cloud Functions or App Engine-specific properties, OR, you can use the
        following generic properties that are compatible with all serverless
        platforms, including API Gateway: serverless-deployment-platform,
        serverless-deployment-resource, serverless-deployment-url-mask, and
        serverless-deployment-version.
    """
    serverless_deployment_group = serverless_group.add_group(
        help=serverless_deployment_group_help
    )
    serverless_deployment_platform_help = """\
        The platform of the NEG backend target(s). Possible values:

          * API Gateway: apigateway.googleapis.com
          * App Engine: appengine.googleapis.com
          * Cloud Functions: cloudfunctions.googleapis.com
          * Cloud Run: run.googleapis.com
    """
    serverless_deployment_group.add_argument(
        '--serverless-deployment-platform',
        help=serverless_deployment_platform_help,
    )
    serverless_deployment_resource_help = """\
        The user-defined name of the workload/instance. This value must be
        provided explicitly or using the --serverless-deployment-url-mask
        option. The resource identified by this value is platform-specific and
        is as follows:

          * API Gateway: The gateway ID
          * App Engine: The service name
          * Cloud Functions: The function name
          * Cloud Run: The service name
    """
    serverless_deployment_group.add_argument(
        '--serverless-deployment-resource',
        help=serverless_deployment_resource_help,
    )
    serverless_deployment_version_help = """\
        The optional resource version. The version identified by this value is
        platform-specific and is as follows:

          * API Gateway: Unused
          * App Engine: The service version
          * Cloud Functions: Unused
          * Cloud Run: The service tag
    """
    serverless_deployment_group.add_argument(
        '--serverless-deployment-version',
        help=serverless_deployment_version_help,
    )
    serverless_deployment_url_mask_help = """\
        A template to parse platform-specific fields from a request URL. URL
        mask allows for routing to multiple resources on the same serverless
        platform without having to create multiple network endpoint groups and
        backend resources. The fields parsed by this template are
        platform-specific and are as follows:

          * API Gateway: The 'gateway' ID
          * App Engine: The 'service' and 'version'
          * Cloud Functions: The 'function' name
          * Cloud Run: The 'service' and 'tag'
    """
    serverless_deployment_group.add_argument(
        '--serverless-deployment-url-mask',
        help=serverless_deployment_url_mask_help,
    )


def _AddL7pscRoutingInfo(parser):
  """Adds l7psc routing info arguments for PSC network endpoint groups."""

  psc_target_service_help = """\
      PSC target service name to add to the private service connect network
      endpoint groups (NEG).
  """
  parser.add_argument('--psc-target-service', help=psc_target_service_help)


def _AddPortMappingInfo(parser):
  """Adds port mapping info arguments for network endpoint groups."""

  help_text = """
  Determines the spec of client port maping mode of this group.
  Port Mapping is a use case in which NEG specifies routing by mapping client ports to destinations (e.g. ip and port).

  *port-mapping-disabled*:::
  Group should not be used for mapping client port to destination.

  *client-port-per-endpoint*:::
  For each endpoint there is exactly one client port.
  """

  parser.add_argument(
      '--client-port-mapping-mode',
      help=help_text,
  )


def AddCreateNegArgsToParser(
    parser,
    support_neg_type=False,
    support_serverless_deployment=False,
    support_port_mapping_neg=False,
):
  """Adds flags for creating a network endpoint group to the parser."""

  _AddNetworkEndpointGroupType(parser, support_neg_type)
  _AddNetworkEndpointType(parser)
  _AddNetwork(parser)
  _AddSubnet(parser)
  _AddDefaultPort(parser)
  _AddServerlessRoutingInfo(parser, support_serverless_deployment)
  _AddL7pscRoutingInfo(parser)
  if support_port_mapping_neg:
    _AddPortMappingInfo(parser)


def _AddAddEndpoint(
    endpoint_group, endpoint_spec, support_ipv6, support_port_mapping_neg
):
  """Adds add endpoint argument for updating network endpoint groups."""
  help_text = """\
          The network endpoint to add to the network endpoint group. Keys used
          depend on the endpoint type of the NEG.

          `gce-vm-ip-port`

              *instance* - Name of instance in same zone as the network endpoint
              group.

              The VM instance must belong to the network / subnetwork
              associated with the network endpoint group. If the VM instance
              is deleted, then any network endpoint group that has a reference
              to it is updated.

              *ip* - Optional IP address of the network endpoint. The IP address
              must belong to a VM in compute engine (either the primary IP or
              as part of an aliased IP range). If the IP address is not
              specified, then the primary IP address for the VM instance in
              the network that the network endpoint group belongs to is
              used.
              """

  if support_ipv6:
    help_text += """\

              *ipv6* - Optional IPv6 address of the network endpoint. The IPv6
              address must belong to a VM in compute engine (either the internal
              or external IPv6 address).

              At least one of the ip and ipv6 must be specified.
                 """
  help_text += """\

              *port* - Required endpoint port unless NEG default port is set.
               """
  if support_port_mapping_neg:
    help_text += """\

              *client-port* - Required endpoint client port only for the port
              mapping NEG.
               """

  help_text += """\

          `internet-ip-port`
               """

  if support_ipv6:
    help_text += """\

              *ip* - Optional IPv4 address of the endpoint to attach. Must be
              publicly routable.

              *ipv6* - Optional IPv6 address of the endpoint to attach. Must be
              publicly routable.

              At least one of the ip and ipv6 must be specified.
            """
  else:
    help_text += """\

              *ip* - Required IPv4 address of the endpoint to attach. Must be
              publicly routable.
            """

  help_text += """\

              *port* - Optional port of the endpoint to attach. If unspecified,
              the NEG default port is set. If no default port is set, the
              well-known port for the backend protocol is used instead
              (80 for HTTP, 443 for HTTPS).

          `internet-fqdn-port`

              *fqdn* - Required fully qualified domain name to use to look up an
              external endpoint. Must be resolvable to a public IP address via
              public DNS.

              *port* - Optional port of the endpoint to attach. If unspecified,
              the NEG default port is set. If no default port is set, the
              well-known port for the backend protocol is used instead
              (80 for HTTP, 443 for HTTPS or HTTP2).

              Example: `--add-endpoint="fqdn=backend.example.com,port=443"`

          `non-gcp-private-ip-port`

    """
  if support_ipv6:
    help_text += """\

              *ip* - Optional IPv4 address of the network endpoint to attach.
              The IP address must belong to a VM not in Compute Engine and must
              be routable using a Cloud Router over VPN or an Interconnect
              connection.

              *ipv6* - Optional IPv6 address of the network endpoint to attach.
              The IP address must belong to a VM not in Compute Engine and must
              be routable using a Cloud Router over VPN or an Interconnect
              connection.

              At least one of the ip and ipv6 must be specified.
      """
  else:
    help_text += """\

              *ip* - Required IPv4 address of the network endpoint to attach.
              The IP address must belong to a VM not in Compute Engine and must
              be routable using a Cloud Router over VPN or an Interconnect
              connection.
      """

  help_text += """\

              *port* - Required port of the network endpoint to attach unless
              the NEG default port is set.

          `gce-vm-ip`

              *instance* - Required instance name in same zone as the network
              endpoint group.

              The VM instance must belong to the network / subnetwork
              associated with the network endpoint group. If the VM instance
              is deleted, then any network endpoint group that has a reference
              to it is updated.

              *ip* - Optional IP address of the network endpoint to attach. The
              IP address must be the VM's network interface address. If not
              specified, the primary NIC address is used.
    """

  endpoint_group.add_argument(
      '--add-endpoint',
      action='append',
      type=arg_parsers.ArgDict(spec=endpoint_spec),
      help=help_text,
  )


def _AddRemoveEndpoint(
    endpoint_group, endpoint_spec, support_ipv6, support_port_mapping_neg
):
  """Adds remove endpoint argument for updating network endpoint groups."""
  help_text = """\
          The network endpoint to detach from the network endpoint group. Keys
          used depend on the endpoint type of the NEG.

          `gce-vm-ip-port`

              *instance* - Required name of instance whose endpoint(s) to
              detach. If the IP address is unset, all endpoints for the
              instance in the NEG are detached.

              *ip* - Optional IPv4 address of the network endpoint to detach.
              If specified port must be provided as well.
  """
  if support_ipv6:
    help_text += """\

              *ipv6* - Optional IPv6 address of the network endpoint to detach.
              If specified port must be provided as well.
    """
  help_text += """\

              *port* - Optional port of the network endpoint to detach.
    """

  if support_port_mapping_neg:
    help_text += """\

              *client-port* - Optional client port, only for port mapping NEGs.
               """

  help_text += """\

          `internet-ip-port`

              *ip* - Required IPv4 address of the network endpoint to detach.
  """

  if support_ipv6:
    help_text += """\

              *ipv6* - Required IPv6 address of the network endpoint to detach.

              At least one of the ip and ipv6 must be specified.
    """

  help_text += """\

              *port* - Optional port of the network endpoint to detach if the
              endpoint has a port specified.

          `internet-fqdn-port`

              *fqdn* - Required fully qualified domain name of the endpoint to
              detach.

              *port* - Optional port of the network endpoint to detach if the
              endpoint has a port specified.

          `non-gcp-private-ip-port`

              *ip* - Required IPv4 address of the network endpoint to detach.
    """

  if support_ipv6:
    help_text += """\

              *ipv6* - Required IPv6 address of the network endpoint to detach.

              At least one of the ip and ipv6 must be specified.
      """

  help_text += """\

              *port* - Required port of the network endpoint to detach unless
              NEG default port is set.

          `gce-vm-ip`

              *instance* - Required name of instance with endpoints to
              detach. If the IP address is unset, all endpoints for the
              instance in the NEG are detached.

              *ip* - Optional IP address of the network endpoint to attach. The
              IP address must be the VM's network interface's primary IP
              address. If not specified, the primary NIC address is used.
  """

  endpoint_group.add_argument(
      '--remove-endpoint',
      action='append',
      type=arg_parsers.ArgDict(spec=endpoint_spec),
      help=help_text,
  )


def AddUpdateNegArgsToParser(
    parser, support_ipv6=False, support_port_mapping_neg=False
):
  """Adds flags for updating a network endpoint group to the parser."""
  endpoint_group = parser.add_group(
      mutex=True,
      required=True,
      help=(
          'These flags can be specified multiple times to add/remove '
          'multiple endpoints.'
      ),
  )

  endpoint_spec = {'instance': str, 'ip': str, 'port': int, 'fqdn': str}
  if support_ipv6:
    endpoint_spec['ipv6'] = str
  if support_port_mapping_neg:
    endpoint_spec['client-port'] = int
  _AddAddEndpoint(
      endpoint_group, endpoint_spec, support_ipv6, support_port_mapping_neg
  )
  _AddRemoveEndpoint(
      endpoint_group, endpoint_spec, support_ipv6, support_port_mapping_neg
  )
