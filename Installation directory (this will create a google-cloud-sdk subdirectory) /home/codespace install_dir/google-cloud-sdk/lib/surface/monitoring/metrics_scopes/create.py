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
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Create a monitored project in a metrics scope.

  This command can fail for the following reasons:
  * The projects specified do not exist.
  * The active account does not have permission to access one of the given
  project.
  * The monitored project already exists in the metrics scope.

  More details can be found at
  https://cloud.google.com/monitoring/api/ref_v3/rest/v1/locations.global.metricsScopes.projects/create

  ## EXAMPLES

  The following command adds a monitored project with the ID
  `monitored-project-1` to a metrics scope with project id `metrics-scope-1`
  assuming the `metrics-scope-1` is the default project:

    $ {command} projects/monitored-project-1

  The following command adds a monitored project with the ID
  `monitored-project-1` to a metrics scope with project id `metrics-scope-1`:

    $ {command} projects/monitored-project-1 --project=metrics-scope-1
    $ {command}
    locations/global/metricsScopes/metrics-scope-1/projects/monitored-project-1
  """

  @staticmethod
  def Args(parser):
    flags.GetMonitoredResourceContainerNameFlag('create').AddToParser(parser)

  def Run(self, args):
    client = metrics_scopes.MetricsScopeClient()
    metrics_scope_def, monitored_project_ref = (
        monitoring_util.ParseMonitoredProject(
            args.monitored_resource_container_name, True
        )
    )
    result = client.Create(metrics_scope_def, monitored_project_ref)
    log.CreatedResource(
        client.MonitoredProjectName(metrics_scope_def, monitored_project_ref),
        'monitored project')
    return result
