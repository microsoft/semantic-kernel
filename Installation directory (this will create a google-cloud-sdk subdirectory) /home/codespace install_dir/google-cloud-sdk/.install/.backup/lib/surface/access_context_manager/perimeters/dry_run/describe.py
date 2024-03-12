# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""`gcloud access-context-manager perimeters dry-run describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class DescribePerimeterDryRun(base.DescribeCommand):
  """Displays the dry-run mode configuration for a Service Perimeter."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to describe')

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    perimeter = client.Get(perimeter_ref)
    perimeters.GenerateDryRunConfigDiff(perimeter, self._API_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribePerimeterDryRunAlpha(DescribePerimeterDryRun):
  """Displays the dry-run mode configuration for a Service Perimeter."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief':
        'Display the dry-run mode configuration for a Service Perimeter.',
    'DESCRIPTION':
        ('The dry-run mode configuration is presented as a diff against the '
         'enforcement mode configuration. \'+\' indicates additions in `spec`,'
         '\'-\' indicates removals from `status` and entries without either of '
         'those indicate that they are the same across the dry-run and the '
         'enforcement mode configurations. When a particular field is '
         'completely empty, it will not be displayed.\n\nNote: When this '
         'command is executed on a Service Perimeter with no explicit dry-run '
         'mode configuration, the effective dry-run mode configuration is '
         'inherited from the enforcement mode configuration, and thus, the '
         'enforcement mode configuration is displayed in such cases.'),
    'EXAMPLES': ("""\
To display the dry-run mode configuration for a Service Perimeter:

  $ {command} my-perimeter

Sample output:

 ===
   name: my_perimeter
   title: My Perimeter
   type: PERIMETER_TYPE_REGULAR
   resources:
 +   projects/123
 -   projects/456
     projects/789
   restrictedServices:
 +   bigquery.googleapis.com
 -   storage.googleapis.com
     bigtable.googleapis.com
   vpcAccessibleServices:
 +   allowedServices:
 +     bigquery.googleapis.com
 -     storage.googleapis.com
 +   enableRestriction: true
""")
}

DescribePerimeterDryRunAlpha.detailed_help = detailed_help
DescribePerimeterDryRun.detailed_help = detailed_help
