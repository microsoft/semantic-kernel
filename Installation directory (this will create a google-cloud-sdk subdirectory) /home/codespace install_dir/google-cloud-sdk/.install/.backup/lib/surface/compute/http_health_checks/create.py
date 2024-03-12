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
"""Command for creating HTTP health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.http_health_checks import flags


class Create(base.CreateCommand):
  """Create a legacy HTTP health check.

  Legacy HTTP health checks are required if you want to implement health
  checking for a target pool backend of an external passthrough Network
  Load Balancer. Though you can
  use legacy HTTP health checks in certain other Google Cloud Platform load
  balancing configurations and for managed instance group autohealing, you
  should consider a non-legacy HTTP health check created with `health-checks
  create http` instead.

  For more information about the differences between legacy and non-legacy
  health checks see:
  [](https://cloud.google.com/load-balancing/docs/health-check-concepts#category_and_protocol)

  For information about what type of health check to use for a particular load
  balancer, see:
  [](https://cloud.google.com/load-balancing/docs/health-check-concepts#lb_guide)
  """

  HTTP_HEALTH_CHECKS_ARG = None

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.HTTP_HEALTH_CHECKS_ARG = flags.HttpHealthCheckArgument()
    cls.HTTP_HEALTH_CHECKS_ARG.AddArgument(parser, operation_type='create')
    parser.display_info.AddCacheUpdater(completers.HttpHealthChecksCompleter)

    parser.add_argument(
        '--host',
        help="""\
        The value of the host header used in this HTTP health check request.
        By default, this is empty and Compute Engine automatically sets
        the host header in health requests to the same external IP address as
        the forwarding rule associated with the target pool.
        """)

    parser.add_argument(
        '--port',
        type=int,
        default=80,
        help="""\
        The TCP port number that this health check monitors. The default value
        is 80.
        """)

    parser.add_argument(
        '--request-path',
        default='/',
        help="""\
        The request path that this health check monitors. For example,
        ``/healthcheck''. The default value is ``/''.
        """)

    parser.add_argument(
        '--check-interval',
        type=arg_parsers.Duration(),
        default='5s',
        help="""\
        How often to perform a health check for an instance. For example,
        specifying ``10s'' will run the check every 10 seconds. The default
        value is ``5s''. See $ gcloud topic datetimes for information on
        duration formats.
        """)

    parser.add_argument(
        '--timeout',
        type=arg_parsers.Duration(),
        default='5s',
        help="""\
        If Compute Engine doesn't receive an HTTP 200 response from the
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
        help='An optional, textual description for the HTTP health check.')

  def Run(self, args):
    """Issues the request necessary for adding the health check."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    health_check_ref = self.HTTP_HEALTH_CHECKS_ARG.ResolveAsResource(
        args, holder.resources)

    request = client.messages.ComputeHttpHealthChecksInsertRequest(
        httpHealthCheck=client.messages.HttpHealthCheck(
            name=health_check_ref.Name(),
            host=args.host,
            port=args.port,
            description=args.description,
            requestPath=args.request_path,
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold,
        ),
        project=health_check_ref.project)

    return client.MakeRequests([(client.apitools_client.httpHealthChecks,
                                 'Insert', request)])
