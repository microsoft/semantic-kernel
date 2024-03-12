# pylint: disable=E1305
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

"""Flags and helpers for the compute backend-services backend commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import log


def AddDescription(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend.')


def AddInstanceGroup(parser, operation_type, with_deprecated_zone=False):
  """Adds arguments to define instance group."""
  parser.add_argument(
      '--instance-group',
      required=True,
      help='The name or URI of a Google Cloud Instance Group.')

  scope_parser = parser.add_mutually_exclusive_group()
  flags.AddRegionFlag(
      scope_parser,
      resource_type='instance group',
      operation_type='{0} the backend service'.format(operation_type),
      flag_prefix='instance-group',
      explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
  if with_deprecated_zone:
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='{0} the backend service'.format(operation_type),
        explanation='DEPRECATED, use --instance-group-zone flag instead.')
  flags.AddZoneFlag(
      scope_parser,
      resource_type='instance group',
      operation_type='{0} the backend service'.format(operation_type),
      flag_prefix='instance-group',
      explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)


def WarnOnDeprecatedFlags(args):
  if getattr(args, 'zone', None):  # TODO(b/28518663).
    log.warning(
        'The --zone flag is deprecated, please use --instance-group-zone'
        ' instead. It will be removed in a future release.')


def _GetBalancingModes():
  """Returns the --balancing-modes flag value choices name:description dict."""
  per_rate_flags = '*--max-rate-per-instance*'
  per_connection_flags = '*--max-connections-per-instance*'
  per_rate_flags += '/*--max-rate-per-endpoint*'
  per_connection_flags += '*--max-max-per-endpoint*'
  utilization_extra_help = (
      'This is incompatible with --network-endpoint-group.')
  balancing_modes = {
      'CONNECTION': textwrap.dedent("""
          Available if the backend service's load balancing scheme is either
          `INTERNAL` or `EXTERNAL`.
          Available if the backend service's protocol is one of `SSL`, `TCP`,
          or `UDP`.

          Spreads load based on how many concurrent connections the backend
          can handle.

          For backend services with --load-balancing-scheme `EXTERNAL`, you
          must specify exactly one of these additional parameters:
          `--max-connections`, `--max-connections-per-instance`, or
          `--max-connections-per-endpoint`.

          For backend services where `--load-balancing-scheme` is `INTERNAL`,
          you must omit all of these parameters.
          """).format(per_rate_flags),
      'RATE': textwrap.dedent("""
          Available if the backend service's load balancing scheme is
          `INTERNAL_MANAGED`, `INTERNAL_SELF_MANAGED`, or `EXTERNAL`. Available
          if the backend service's protocol is one of HTTP, HTTPS, or HTTP/2.

          Spreads load based on how many HTTP requests per second (RPS) the
          backend can handle.

          You must specify exactly one of these additional parameters:
          `--max-rate`, `--max-rate-per-instance`, or `--max-rate-per-endpoint`.
          """).format(utilization_extra_help),
      'UTILIZATION': textwrap.dedent("""
          Available if the backend service's load balancing scheme is
          `INTERNAL_MANAGED`, `INTERNAL_SELF_MANAGED`, or `EXTERNAL`. Available only
          for managed or unmanaged instance group backends.

          Spreads load based on the backend utilization of instances in a backend
          instance group.

          The following additional parameters may be specified:
          `--max-utilization`, `--max-rate`, `--max-rate-per-instance`,
          `--max-connections`, `--max-connections-per-instance`.
          For valid combinations, see `--max-utilization`.
          """).format(per_connection_flags),
  }
  return balancing_modes


def AddBalancingMode(parser,
                     support_global_neg=False,
                     support_region_neg=False):
  """Adds balancing mode argument to the argparse."""
  help_text = """\
  Defines how to measure whether a backend can handle additional traffic or is
  fully loaded. For more information, see
  https://cloud.google.com/load-balancing/docs/backend-service#balancing-mode.
  """
  incompatible_types = []
  if support_global_neg:
    incompatible_types.extend(['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT'])
  if support_region_neg:
    incompatible_types.append('SERVERLESS')
  if incompatible_types:
    help_text += """\

  This cannot be used when the endpoint type of an attached network endpoint
  group is {0}.
    """.format(_JoinTypes(incompatible_types))
  parser.add_argument(
      '--balancing-mode',
      choices=_GetBalancingModes(),
      type=lambda x: x.upper(),
      help=help_text)


def AddCapacityLimits(parser,
                      support_global_neg=False,
                      support_region_neg=False):
  """Adds capacity thresholds arguments to the argparse."""
  AddMaxUtilization(parser)
  capacity_group = parser.add_group(mutex=True)
  capacity_incompatible_types = []
  if support_global_neg:
    capacity_incompatible_types.extend(
        ['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT'])
  if support_region_neg:
    capacity_incompatible_types.append('SERVERLESS')
  append_help_text = """\

  This cannot be used when the endpoint type of an attached network endpoint
  group is {0}.
  """.format(_JoinTypes(
      capacity_incompatible_types)) if capacity_incompatible_types else ''
  capacity_group.add_argument(
      '--max-rate-per-endpoint',
      type=float,
      help="""\
      Only valid for network endpoint group backends. Defines a maximum
      number of HTTP requests per second (RPS) per endpoint if all endpoints
      are healthy. When one or more endpoints are unhealthy, an effective
      maximum rate per healthy endpoint is calculated by multiplying
      `MAX_RATE_PER_ENDPOINT` by the number of endpoints in the network
      endpoint group, and then dividing by the number of healthy endpoints.
      """ + append_help_text)
  capacity_group.add_argument(
      '--max-connections-per-endpoint',
      type=int,
      help="""\
      Only valid for network endpoint group backends. Defines a maximum
      number of connections per endpoint if all endpoints are healthy. When
      one or more endpoints are unhealthy, an effective maximum average number
      of connections per healthy endpoint is calculated by multiplying
      `MAX_CONNECTIONS_PER_ENDPOINT` by the number of endpoints in the network
      endpoint group, and then dividing by the number of healthy endpoints.
      """ + append_help_text)

  capacity_group.add_argument(
      '--max-rate',
      type=int,
      help="""\
      Maximum number of HTTP requests per second (RPS) that the backend can
      handle. Valid for network endpoint group and instance group backends
      (except for regional managed instance groups). Must not be defined if the
      backend is a managed instance group using load balancing-based autoscaling.
      """ + append_help_text)
  capacity_group.add_argument(
      '--max-rate-per-instance',
      type=float,
      help="""\
      Only valid for instance group backends. Defines a maximum number of
      HTTP requests per second (RPS) per instance if all instances in the
      instance group are healthy. When one or more instances are unhealthy,
      an effective maximum RPS per healthy instance is calculated by
      multiplying `MAX_RATE_PER_INSTANCE` by the number of instances in the
      instance group, and then dividing by the number of healthy instances. This
      parameter is compatible with managed instance group backends that use
      autoscaling based on load balancing.
      """)
  capacity_group.add_argument(
      '--max-connections',
      type=int,
      help="""\
      Maximum concurrent connections that the backend can handle. Valid for
      network endpoint group and instance group backends (except for regional
      managed instance groups).
      """ + append_help_text)
  capacity_group.add_argument(
      '--max-connections-per-instance',
      type=int,
      help="""\
      Only valid for instance group backends. Defines a maximum number
      of concurrent connections per instance if all instances in the
      instance group are healthy. When one or more instances are
      unhealthy, an effective average maximum number of connections per healthy
      instance is calculated by multiplying `MAX_CONNECTIONS_PER_INSTANCE`
      by the number of instances in the instance group, and then dividing by
      the number of healthy instances.
      """)


def AddMaxUtilization(parser):
  """Adds max utilization argument to the argparse."""
  parser.add_argument(
      '--max-utilization',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      Defines the maximum target for average utilization of the backend instance
      group. Supported values are `0.0` (0%) through `1.0` (100%). This is an
      optional parameter for the `UTILIZATION` balancing mode.

      You can use this parameter with other parameters for defining target
      capacity. For usage guidelines, see
      [Balancing mode combinations](https://cloud.google.com/load-balancing/docs/backend-service#balancing-mode-combos).
      """)


def AddCapacityScalar(parser,
                      support_global_neg=False,
                      support_region_neg=False):
  """Adds capacity thresholds argument to the argparse."""
  help_text = """\
      Scales down the target capacity (max utilization, max rate, or max
      connections) without changing the target capacity. For usage guidelines
      and examples, see
      [Capacity scaler](https://cloud.google.com/load-balancing/docs/backend-service#capacity_scaler).
      """
  incompatible_types = []
  if support_global_neg:
    incompatible_types.extend(['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT'])
  if support_region_neg:
    incompatible_types.append('SERVERLESS')
  if incompatible_types:
    help_text += """\

    This cannot be used when the endpoint type of an attached network endpoint
    group is {0}.
    """.format(_JoinTypes(incompatible_types))
  parser.add_argument(
      '--capacity-scaler',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help=help_text)


def AddFailover(parser, default):
  """Adds the failover argument to the argparse."""
  parser.add_argument(
      '--failover',
      action='store_true',
      default=default,
      help="""\
      Designates whether this is a failover backend. More than one
      failover backend can be configured for a given BackendService.
      Not compatible with the --global flag""")


def _GetPreference():
  """Returns the --preference flag value choices name:description dict."""
  preferences = {
      'DEFAULT': textwrap.dedent("""
          This is the default setting. If the designated preferred backends
          don't have enough capacity, backends in the default category are used.
          Traffic is distributed between default backends based on the load
          balancing algorithm you use.
          """),
      'PREFERRED': textwrap.dedent("""
          Backends with this preference setting are used up to their capacity
          limits first, while optimizing overall network latency.
          """),
  }
  return preferences


def AddPreference(parser):
  """Adds preference argument to the argparse."""
  help_text = """\
  Defines whether a backend should be fully utilized before
  sending traffic to backends with default preference.
  """
  incompatible_types = ['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT', 'SERVERLESS']
  help_text += """\
  This parameter cannot be used with regional managed instance groups and when
  the endpoint type of an attached network endpoint group is {0}.
  """.format(_JoinTypes(incompatible_types))
  parser.add_argument(
      '--preference',
      choices=_GetPreference(),
      type=lambda x: x.upper(),
      help=help_text)


def _JoinTypes(types):
  return ', or '.join([', '.join(types[:-1]), types[-1]
                      ]) if len(types) > 2 else ' or '.join(types)
