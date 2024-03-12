# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for listing images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.containeranalysis import util as containeranalysis_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.images import flags as image_flags
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List Google occurrences of PACKAGE_VULNERABILITY.

  Lists occurrences with the "kind" field set to "PACKAGE_VULNERABILITY".

  The default value of the `--filter` flag for this command is:

      vulnerabilityDetails.packageIssue.fixedLocation.version.kind != "MAXIMUM"

  so that only vulnerabilities with a known fix are shown. Passing `--filter`
  will override this so *all* PACKAGE_VULNERABILITY occurrences are shown, with
  any additional provided filters applied.
  """

  @staticmethod
  def Args(parser):
    lister.AddBaseListerArgs(parser)
    parser.display_info.AddFormat("""\
        table(
          name,
          noteName.basename():label=NOTE,
          vulnerabilityDetails.severity,
          vulnerabilityDetails.cvssScore,
          vulnerabilityDetails.packageIssue.affectedLocation.package.join(','):label=PACKAGES
        )""")
    List._image_arg = image_flags.MakeDiskImageArg(
        required=False, name='--image')
    List._image_arg.AddArgument(parser, operation_type='create')
    # This allows the occurrence if ANY of its PackageIssues have
    # fixedLocation.version.kind != MAXIMUM.
    # TODO(b/72375279): Do server-side
    parser.display_info.AddFilter(
        'vulnerabilityDetails.packageIssue.fixedLocation.version.kind != '
        '"MAXIMUM"')

  def _GetFilter(self, args, holder):
    filters = [
        'kind = "PACKAGE_VULNERABILITY"',  # Display only vulnerabilities
        # Display only compute metadata
        'has_prefix(resource_url,"https://compute.googleapis.com/compute/")',
    ]
    if args.image:
      image_ref = self._image_arg.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(
              holder.client))
      image_url = image_ref.SelfLink()

      filters.append('has_prefix(resource_url, "{}")'.format(image_url))
    return ' AND '.join(filters)

  def Run(self, args):
    """Yields filtered vulnerabilities."""
    project = properties.VALUES.core.project.Get()
    holder = base_classes.ComputeApiHolder(base.ReleaseTrack.GA)
    resource_filter = self._GetFilter(args, holder)

    return containeranalysis_util.MakeOccurrenceRequest(
        project_id=project, resource_filter=resource_filter,
        occurrence_filter=None, resource_urls=None)
