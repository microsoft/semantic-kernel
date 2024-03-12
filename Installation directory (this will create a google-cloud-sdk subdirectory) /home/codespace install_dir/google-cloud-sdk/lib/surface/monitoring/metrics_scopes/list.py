# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to create a monitored project in a metrics scope."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import metrics_scopes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import util as monitoring_util
from googlecloudsdk.command_lib.projects import util as command_lib_util


class List(base.ListCommand):
  """List the metrics scopes monitoring the specified monitored resource container.

  This command can fail for the following reasons:
  * The projects specified do not exist.
  * The active account does not have permission to access one of the given
  project.

  More details can be found at
  https://cloud.google.com/monitoring/api/ref_v3/rest/v1/locations.global.metricsScopes/listMetricsScopesByMonitoredProject

  ## EXAMPLES
  To list the metrics scopes monitoring MY-PROJECT-ID

  $ {command} projects/MY-PROJECT-ID
  """

  @staticmethod
  def Args(parser):
    flags.GetMonitoredResourceContainerNameFlag('list').AddToParser(parser)

  def Run(self, args):
    client = metrics_scopes.MetricsScopeClient()
    _, resource_id = monitoring_util.ParseMonitoredResourceContainer(
        args.monitored_resource_container_name, True
    )
    project_ref = command_lib_util.ParseProject(resource_id)
    result = client.List(project_ref)
    return result
