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
"""Command for describing health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.health_checks import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Display detailed information about a health check.

  *{command}* displays all data associated with a Google Compute
  Engine health check in a project.
  """

  HEALTH_CHECK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.HEALTH_CHECK_ARG = flags.HealthCheckArgument('')
    cls.HEALTH_CHECK_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    health_check_ref = self.HEALTH_CHECK_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
      request = client.messages.ComputeRegionHealthChecksGetRequest(
          **health_check_ref.AsDict())
      collection = client.apitools_client.regionHealthChecks
    else:
      request = client.messages.ComputeHealthChecksGetRequest(
          **health_check_ref.AsDict())
      collection = client.apitools_client.healthChecks

    return client.MakeRequests([(collection, 'Get', request)])[0]
