# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for listing instance vulnerabilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.containeranalysis import util as containeranalysis_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List vulnerability occurrences for instances.

  Lists occurrences with the "kind" field set to "PACKAGE_VULNERABILITY".
  """

  _INSTANCE_ARG = compute_flags.ResourceArgument(
      resource_name='instance',
      name='--instance',
      completer=compute_completers.InstancesCompleter,
      required=False,
      zonal_collection='compute.instances',
      short_help='The name of the instance to show vulnerabilities for.',
      zone_explanation='If not specified, it will be set to the same as zone.')

  @staticmethod
  def Args(parser):
    List._INSTANCE_ARG.AddArgument(parser)

    parser.display_info.AddFormat("""\
        table(
          name.basename(),
          resource_url.basename():label=INSTANCE,
          resource_url.scope().split('/').slice(0).join(''):label=ZONE,
          noteName.basename():label=NOTE,
          vulnerabilityDetails.severity,
          vulnerabilityDetails.packageIssue.affectedLocation.package.join(','):label=PACKAGES
        )""")

  def _GetFilter(self, project, args, holder):
    filters = [
        'kind = "PACKAGE_VULNERABILITY"',  # Display only vulnerabilities
    ]

    prefix = 'https://www.googleapis.com/compute/projects/{}/zones/'.format(
        project)
    if args.instance:
      inst = List._INSTANCE_ARG.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
      )
      prefix = 'https://www.googleapis.com/compute/{}'.format(
          inst.RelativeName())

    filters.append('has_prefix(resource_url, "{}")'.format(prefix))

    return ' AND '.join(filters)

  def Run(self, args):
    """Yields filtered vulnerabilities."""
    project = properties.VALUES.core.project.Get()
    holder = base_classes.ComputeApiHolder(base.ReleaseTrack.ALPHA)
    resource_filter = self._GetFilter(project, args, holder)

    return containeranalysis_util.MakeOccurrenceRequest(
        project_id=project,
        resource_filter=resource_filter,
        occurrence_filter=None,
        resource_urls=None)
