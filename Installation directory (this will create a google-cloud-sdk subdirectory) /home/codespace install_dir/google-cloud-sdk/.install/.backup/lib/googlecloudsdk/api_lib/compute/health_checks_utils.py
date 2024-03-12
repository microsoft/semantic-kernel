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
"""Code that's shared between multiple health-checks subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.health_checks import exceptions as hc_exceptions


THRESHOLD_UPPER_BOUND = 10
THRESHOLD_LOWER_BOUND = 1
TIMEOUT_UPPER_BOUND_SEC = 300
TIMEOUT_LOWER_BOUND_SEC = 1
CHECK_INTERVAL_UPPER_BOUND_SEC = 300
CHECK_INTERVAL_LOWER_BOUND_SEC = 1


def AddProtocolAgnosticCreationArgs(parser, protocol_string):
  """Adds parser arguments common to creation for all protocols."""

  parser.add_argument(
      '--check-interval',
      type=arg_parsers.Duration(),
      default='5s',
      help="""\
      How often to perform a health check for an instance. For example,
      specifying ``10s'' will run the check every 10 seconds. The default
      value is ``5s''.
      See $ gcloud topic datetimes for information on duration formats.
       """)

  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      default='5s',
      help="""\
      If Google Compute Engine doesn't receive a healthy response from the
      instance by the time specified by the value of this flag, the health
      check request is considered a failure. For example, specifying ``10s''
      will cause the check to wait for 10 seconds before considering the
      request a failure. The default value is ``5s''.
      See $ gcloud topic datetimes for information on duration formats.
      """)

  parser.add_argument(
      '--unhealthy-threshold',
      type=int,
      default=2,
      help="""\
      The number of consecutive health check failures before a healthy
      instance is marked as unhealthy. The default is 2.
      """)

  parser.add_argument(
      '--healthy-threshold',
      type=int,
      default=2,
      help="""\
      The number of consecutive successful health checks before an
      unhealthy instance is marked as healthy. The default is 2.
      """)

  parser.add_argument(
      '--description',
      help="""\
      An optional string description for the """ + protocol_string + """ health
      check.
      """)


def AddProtocolAgnosticUpdateArgs(parser, protocol_string):
  """Adds parser arguments common to update subcommand for all protocols."""

  parser.add_argument(
      '--check-interval',
      type=arg_parsers.Duration(),
      help="""\
      How often to perform a health check for an instance. For example,
      specifying ``10s'' will run the check every 10 seconds.
      See $ gcloud topic datetimes for information on duration formats.
      """)

  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      help="""\
      If Google Compute Engine doesn't receive a healthy response from the
      instance by the time specified by the value of this flag, the health
      check request is considered a failure. For example, specifying ``10s''
      will cause the check to wait for 10 seconds before considering the
      request a failure.
      See $ gcloud topic datetimes for information on duration formats.
      """)

  parser.add_argument(
      '--unhealthy-threshold',
      type=int,
      help="""\
      The number of consecutive health check failures before a healthy
      instance is marked as unhealthy.
      """)

  parser.add_argument(
      '--healthy-threshold',
      type=int,
      help="""\
      The number of consecutive successful health checks before an
      unhealthy instance is marked as healthy.
      """)

  parser.add_argument(
      '--description',
      help=('A textual description for the ' + protocol_string +
            ' health check. Pass in an empty string to unset.'))


def AddHttpRelatedCreationArgs(parser, include_weighted_load_balancing=False):
  """Adds parser arguments for creation related to HTTP."""

  _AddPortRelatedCreationArgs(parser)
  AddProxyHeaderRelatedCreateArgs(parser)

  parser.add_argument(
      '--host',
      help="""\
      The value of the host header used for the health check. If unspecified,
      Google Cloud sets the host header to the IP address of the load balancer's
      forwarding rule.
      """)

  parser.add_argument(
      '--request-path',
      default='/',
      help="""\
      The request path that this health check monitors. For example,
      ``/healthcheck''. The default value is ``/''.
      """)

  if include_weighted_load_balancing:
    parser.add_argument(
        '--weight-report-mode',
        choices=['ENABLE', 'DISABLE', 'DRY_RUN'],
        help="""\
        Defines whether Weighted Load Balancing is enabled.
        """)


def AddHttpRelatedResponseArg(parser):
  """Adds parser argument for HTTP response field."""

  parser.add_argument(
      '--response',
      help="""\
      When empty, status code of the response determines health. When not empty,
      presence of specified string in first 1024 characters of response body
      determines health. Only ASCII characters allowed.
      """)


def AddHttpRelatedUpdateArgs(parser, include_weighted_load_balancing=False):
  """Adds parser arguments for update subcommands related to HTTP."""

  _AddPortRelatedUpdateArgs(parser)
  AddProxyHeaderRelatedUpdateArgs(parser)

  parser.add_argument(
      '--host',
      help="""\
      The value of the host header used in this HTTP health check request.
      The host header is empty by default. When empty, the health check will set
      the host header to the IP address of the backend VM or endpoint. You can
      set the host header to an empty value to return to this default behavior.
      """)

  parser.add_argument(
      '--request-path',
      help="""\
      The request path that this health check monitors. For example,
      ``/healthcheck''.
      """)

  if include_weighted_load_balancing:
    parser.add_argument(
        '--weight-report-mode',
        choices=['ENABLE', 'DISABLE', 'DRY_RUN'],
        help="""\
        Defines whether Weighted Load Balancing is enabled.
        """)


def AddTcpRelatedCreationArgs(parser):
  """Adds parser arguments for creation related to TCP."""

  _AddPortRelatedCreationArgs(parser)
  AddProxyHeaderRelatedCreateArgs(parser)
  _AddTcpRelatedArgsImpl(add_info_about_clearing=False, parser=parser)


def AddTcpRelatedUpdateArgs(parser):
  """Adds parser arguments for update subcommands related to TCP."""

  _AddPortRelatedUpdateArgs(parser)
  AddProxyHeaderRelatedUpdateArgs(parser)
  _AddTcpRelatedArgsImpl(add_info_about_clearing=True, parser=parser)


def AddGrpcRelatedCreationArgs(parser):
  """Adds parser arguments for creation related to gRPC."""

  _AddPortRelatedCreationArgs(
      parser,
      use_port_name=False,
      use_serving_port=True,
      port_type='TCP',
      default_port=None)

  parser.add_argument(
      '--grpc-service-name',
      help="""\
      An optional gRPC service name string of up to 1024 characters to include
      in the gRPC health check request. Only ASCII characters are allowed.""")


def AddGrpcRelatedUpdateArgs(parser):
  """Adds parser arguments for update subcommands related to gRPC."""

  _AddPortRelatedUpdateArgs(parser, use_port_name=False)

  parser.add_argument(
      '--grpc-service-name',
      help="""\
      An optional gRPC service name string of up to 1024 characters to include
      in the gRPC health check request. Pass in an empty string to unset.
      Only ASCII characters are allowed.""")


def AddUdpRelatedArgs(parser, request_and_response_required=True):
  """Adds parser arguments related to UDP."""

  _AddPortRelatedCreationArgs(
      parser, use_serving_port=False, port_type='UDP', default_port=None)

  parser.add_argument(
      '--request',
      required=request_and_response_required,
      help="""\
      Application data to send in payload of an UDP packet. It is an error if
      this is empty.
      """)

  parser.add_argument(
      '--response',
      required=request_and_response_required,
      help="""\
      The bytes to match against the beginning of the response data.
      It is an error if this is empty.
      """)


def _AddPortRelatedCreationArgs(parser,
                                use_port_name=True,
                                use_serving_port=True,
                                port_type='TCP',
                                default_port=80):
  """Adds parser create subcommand arguments --port and --port-name."""

  port_group_help = [
      'These flags configure the port that the health check monitors.'
  ]
  if default_port:
    port_group_help.append(
        'If none is specified, the default port of 80 is used.'
    )

  if use_port_name:
    port_group_help.append(
        'If both `--port` and `--port-name` are specified, `--port` takes '
        'precedence.')
  port_group = parser.add_group(help=' '.join(port_group_help))
  port_group.add_argument(
      '--port',
      type=int,
      default=default_port,
      help="""\
      The {} port number that this health check monitors.
      """.format(port_type))

  if use_port_name:
    port_group.add_argument(
        '--port-name',
        help="""\
        The port name that this health check monitors. By default, this is
        empty.
        """)

  if use_serving_port:
    _AddUseServingPortFlag(port_group, use_port_name)


def _AddPortRelatedUpdateArgs(parser, use_port_name=True):
  """Adds parser update subcommand arguments --port and --port-name."""

  port_group = parser.add_group(
      help=('These flags configure the port that the health check monitors.%s' %
            (' If both `--port` and `--port-name` are specified, `--port` takes'
             ' precedence.' if use_port_name else '')))

  port_group.add_argument(
      '--port',
      type=int,
      help='The TCP port number that this health check monitors.')

  if use_port_name:
    port_group.add_argument(
        '--port-name',
        help="""\
        The port name that this health check monitors. By default, this is
        empty. Setting this to an empty string will clear any existing
        port-name value.
        """)

  _AddUseServingPortFlag(port_group, use_port_name)


def _AddTcpRelatedArgsImpl(add_info_about_clearing, parser):
  """Adds TCP-related subcommand parser arguments."""

  request_help = """\
      An optional string of up to 1024 characters to send once the health check
      TCP connection has been established. The health checker then looks for a
      reply of the string provided in the `--response` field.

      If `--response` is not configured, the health checker does not wait for a
      response and regards the probe as successful if the TCP or SSL handshake
      was successful.
      """
  response_help = """\
      An optional string of up to 1024 characters that the health checker
      expects to receive from the instance. If the response is not received
      exactly, the health check probe fails. If `--response` is configured, but
      not `--request`, the health checker will wait for a response anyway.
      Unless your system automatically sends out a message in response to a
      successful handshake, only configure `--response` to match an explicit
      `--request`.
      """

  if add_info_about_clearing:
    request_help += """
      Setting this to an empty string will clear any existing request value.
      """
    response_help += """\
      Setting this to an empty string will clear any existing
      response value.
      """

  parser.add_argument(
      '--request',
      help=request_help)

  parser.add_argument(
      '--response',
      help=response_help)


def AddProxyHeaderRelatedCreateArgs(parser, default='NONE'):
  """Adds parser arguments for creation related to ProxyHeader."""

  parser.add_argument(
      '--proxy-header',
      choices={
          'NONE': 'No proxy header is added.',
          'PROXY_V1': r'Adds the header "PROXY UNKNOWN\r\n".',
      },
      default=default,
      help='The type of proxy protocol header to be sent to the backend.')


def AddProxyHeaderRelatedUpdateArgs(parser):
  """Adds parser arguments for update related to ProxyHeader."""

  AddProxyHeaderRelatedCreateArgs(parser, default=None)


def CheckProtocolAgnosticArgs(args):
  """Raises exception if any protocol-agnostic args are invalid."""

  if (args.check_interval is not None
      and (args.check_interval < CHECK_INTERVAL_LOWER_BOUND_SEC
           or args.check_interval > CHECK_INTERVAL_UPPER_BOUND_SEC)):
    raise hc_exceptions.ArgumentError(
        '[--check-interval] must not be less than {0} second or greater '
        'than {1} seconds; received [{2}] seconds.'.format(
            CHECK_INTERVAL_LOWER_BOUND_SEC, CHECK_INTERVAL_UPPER_BOUND_SEC,
            args.check_interval))

  if (args.timeout is not None
      and (args.timeout < TIMEOUT_LOWER_BOUND_SEC
           or args.timeout > TIMEOUT_UPPER_BOUND_SEC)):
    raise hc_exceptions.ArgumentError(
        '[--timeout] must not be less than {0} second or greater than {1} '
        'seconds; received: [{2}] seconds.'.format(
            TIMEOUT_LOWER_BOUND_SEC, TIMEOUT_UPPER_BOUND_SEC, args.timeout))

  if (args.healthy_threshold is not None
      and (args.healthy_threshold < THRESHOLD_LOWER_BOUND
           or args.healthy_threshold > THRESHOLD_UPPER_BOUND)):
    raise hc_exceptions.ArgumentError(
        '[--healthy-threshold] must be an integer between {0} and {1}, '
        'inclusive; received: [{2}].'.format(THRESHOLD_LOWER_BOUND,
                                             THRESHOLD_UPPER_BOUND,
                                             args.healthy_threshold))

  if (args.unhealthy_threshold is not None
      and (args.unhealthy_threshold < THRESHOLD_LOWER_BOUND
           or args.unhealthy_threshold > THRESHOLD_UPPER_BOUND)):
    raise hc_exceptions.ArgumentError(
        '[--unhealthy-threshold] must be an integer between {0} and {1}, '
        'inclusive; received [{2}].'.format(THRESHOLD_LOWER_BOUND,
                                            THRESHOLD_UPPER_BOUND,
                                            args.unhealthy_threshold))


def _RaiseBadPortSpecificationError(invalid_flag, port_spec_flag,
                                    invalid_value):
  raise calliope_exceptions.InvalidArgumentException(
      port_spec_flag, '{0} cannot be specified when using: {1}.'.format(
          invalid_flag, invalid_value))


def ValidateAndAddPortSpecificationToHealthCheck(args, x_health_check):
  """Modifies the health check as needed and adds port spec to the check."""
  if args.IsSpecified('port_name') and not args.IsSpecified('port'):
    # When only portName is specified (port is unspecified), we should remove
    # port so that its default value doesn't cause port to take precedence.
    x_health_check.port = None
  enum_class = type(x_health_check).PortSpecificationValueValuesEnum
  if args.use_serving_port:
    if args.IsSpecified('port_name'):
      _RaiseBadPortSpecificationError('--port-name', '--use-serving-port',
                                      '--use-serving-port')
    if args.IsSpecified('port'):
      _RaiseBadPortSpecificationError('--port', '--use-serving-port',
                                      '--use-serving-port')
    x_health_check.portSpecification = enum_class.USE_SERVING_PORT
    x_health_check.port = None
  else:
    if args.IsSpecified('port') and args.IsSpecified('port_name'):
      # Fixed port takes precedence over port name.
      x_health_check.portSpecification = enum_class.USE_FIXED_PORT
      x_health_check.portName = None
    elif args.IsSpecified('port_name'):
      x_health_check.portSpecification = enum_class.USE_NAMED_PORT
    else:
      x_health_check.portSpecification = enum_class.USE_FIXED_PORT


def ValidateAndAddPortSpecificationToGRPCHealthCheck(args, x_health_check):
  """Modifies the gRPC health check as needed and adds port specification."""

  enum_class = type(x_health_check).PortSpecificationValueValuesEnum
  if args.use_serving_port:
    if args.IsSpecified('port'):
      _RaiseBadPortSpecificationError('--port', '--use-serving-port',
                                      '--use-serving-port')
    x_health_check.portSpecification = enum_class.USE_SERVING_PORT
    x_health_check.port = None
  else:
    x_health_check.portSpecification = enum_class.USE_FIXED_PORT


def HandlePortRelatedFlagsForUpdate(args, x_health_check):
  """Calculate port, port_name and port_specification for HC update."""
  port = x_health_check.port
  port_name = x_health_check.portName
  port_specification = x_health_check.portSpecification
  enum_class = type(x_health_check).PortSpecificationValueValuesEnum

  if args.use_serving_port:
    if args.IsSpecified('port_name'):
      _RaiseBadPortSpecificationError('--port-name', '--use-serving-port',
                                      '--use-serving-port')
    if args.IsSpecified('port'):
      _RaiseBadPortSpecificationError('--port', '--use-serving-port',
                                      '--use-serving-port')
    port = None
    port_name = None
    port_specification = enum_class.USE_SERVING_PORT

  if args.IsSpecified('port'):
    # Fixed port takes precedence over port name.
    port = args.port
    port_name = None
    port_specification = enum_class.USE_FIXED_PORT
  elif args.IsSpecified('port_name'):
    if args.port_name:
      port = None
      port_name = args.port_name
      port_specification = enum_class.USE_NAMED_PORT
    else:
      # Empty port_name value is used to clear out the field.
      port_name = None
      port_specification = enum_class.USE_FIXED_PORT
  else:
    # Inherited values from existing health check should remain.
    pass

  return port, port_name, port_specification


def HandlePortRelatedFlagsForGRPCUpdate(args, x_health_check):
  """Calculate port and port_specification for gRPC HC update."""
  port = x_health_check.port
  port_specification = x_health_check.portSpecification
  enum_class = type(x_health_check).PortSpecificationValueValuesEnum

  if args.use_serving_port:
    if args.IsSpecified('port'):
      _RaiseBadPortSpecificationError('--port', '--use-serving-port',
                                      '--use-serving-port')
    port = None
    port_specification = enum_class.USE_SERVING_PORT

  if args.IsSpecified('port'):
    port = args.port
    port_specification = enum_class.USE_FIXED_PORT
  else:
    # Inherited values from existing health check should remain.
    pass

  return port, port_specification


def _AddUseServingPortFlag(parser, use_port_name=True):
  """Adds parser argument for using serving port option."""
  parser.add_argument(
      '--use-serving-port',
      action='store_true',
      help="""\
      If given, use the "serving port" for health checks:

        - When health checking network endpoints in a Network Endpoint
          Group, use the port specified with each endpoint.
          `--use-serving-port` must be used when using a Network Endpoint Group
          as a backend as this flag specifies the `portSpecification` option for
          a Health Check object.
        - When health checking other backends, use the port%s of
          the backend service.""" % (' or named port' if use_port_name else ''))


def IsRegionalHealthCheckRef(health_check_ref):
  """Returns True if the health check reference is regional."""

  return health_check_ref.Collection() == 'compute.regionHealthChecks'


def IsGlobalHealthCheckRef(health_check_ref):
  """Returns True if the health check reference is global."""

  return health_check_ref.Collection() == 'compute.healthChecks'


def AddHealthCheckLoggingRelatedArgs(parser):
  """Adds parser arguments for health check log config."""

  # The parser automatically adds support for --no-enable-logging. Argument
  # value is set to false internally, if --no-enable-logging is specified.
  parser.add_argument(
      '--enable-logging',
      action='store_true',
      default=None,
      help="""\
      Enable logging of health check probe results to Stackdriver. Logging is
      disabled by default.

      Use --no-enable-logging to disable logging.""")


def AddHealthCheckSourceRegionsRelatedArgs(parser):
  """Adds parser arguments for health check source regions."""

  parser.add_argument(
      '--source-regions',
      metavar='REGION',
      help="""\
        Define the list of Google Cloud regions from which health checks are
        performed. This option is supported only for global health checks that
        will be referenced by DNS routing policies. If specified, the
        --check-interval field should be at least 30 seconds. The
        --proxy-header and --request fields (for TCP health checks) are not
        supported with this option.

        If --source-regions is specified for a health check, then that health
        check cannot be used by a backend service or by a managed instance
        group (for autohealing).
        """,
      type=arg_parsers.ArgList(min_length=3),
      default=[],
  )


def CreateLogConfig(client, args):
  """Returns a HealthCheckLogconfig message if args are valid."""

  messages = client.messages
  log_config = None
  if args.enable_logging is not None:
    log_config = messages.HealthCheckLogConfig(enable=args.enable_logging)
  return log_config


def ModifyLogConfig(client, args, existing_log_config):
  """Returns a modified HealthCheckLogconfig message."""

  messages = client.messages
  log_config = None
  if not existing_log_config:
    # If log config has not changed then return early.
    if args.enable_logging is None:
      return log_config
    log_config = messages.HealthCheckLogConfig()
  else:
    log_config = copy.deepcopy(existing_log_config)

  if args.enable_logging is not None:
    log_config.enable = args.enable_logging

  return log_config
