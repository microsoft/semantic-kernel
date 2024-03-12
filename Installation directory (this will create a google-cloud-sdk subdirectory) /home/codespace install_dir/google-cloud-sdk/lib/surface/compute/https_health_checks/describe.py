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
"""Command for describing HTTPS health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.https_health_checks import flags


class Describe(base.DescribeCommand):
  """Display detailed information about an HTTPS health check.

  *{command}* displays all data associated with a Google Compute
  Engine HTTPS health check in a project.
  """

  HTTPS_HEALTH_CHECK = None

  @staticmethod
  def Args(parser):
    Describe.HTTPS_HEALTH_CHECK = flags.HttpsHealthCheckArgument()
    Describe.HTTPS_HEALTH_CHECK.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    https_health_check_ref = self.HTTPS_HEALTH_CHECK.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeHttpsHealthChecksGetRequest(
        **https_health_check_ref.AsDict())

    return client.MakeRequests([(client.apitools_client.httpsHealthChecks,
                                 'Get', request)])[0]
