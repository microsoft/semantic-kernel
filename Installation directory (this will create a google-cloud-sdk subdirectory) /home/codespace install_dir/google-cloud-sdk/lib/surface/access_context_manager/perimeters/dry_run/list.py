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
"""`gcloud access-context-manager perimeters dry-run list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ListPerimeterDryRun(base.ListCommand):
  """Lists the effective dry-run configuration across all Service Perimeters."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--policy',
        metavar='policy',
        default=None,
        help="""Policy resource - The access policy you want to list the
                effective dry-run configuration for. This represents a Cloud
                resource.""")
    parser.display_info.AddFormat('yaml(name.basename(), title, spec)')

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    policy_id = policies.GetDefaultPolicy()
    if args.IsSpecified('policy'):
      policy_id = args.policy

    policy_ref = resources.REGISTRY.Parse(
        policy_id, collection='accesscontextmanager.accessPolicies')

    perimeters_to_display = [p for p in client.List(policy_ref)]
    for p in perimeters_to_display:
      # When a Service Perimeter has use_explicit_dry_run_spec set to false, the
      # dry-run spec is implicitly the same as the status. In order to clearly
      # show the user what exactly is being used as the dry-run spec, we set
      # status to None (this list command is only for the dry-run config) and
      # copy over the status to the spec when the spec is absent. We also append
      # an asterisk to the name to signify that these perimeters are not
      # actually identical to what the API returns.
      if not p.useExplicitDryRunSpec:
        p.spec = p.status
        p.name += '*'
      p.status = None
    print('Note: Perimeters marked with \'*\' do not have an explicit `spec`. '
          'Instead, their `status` also acts as the `spec`.')
    return perimeters_to_display


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListPerimeterDryRunAlpha(ListPerimeterDryRun):
  """Lists the effective dry-run configuration across all Service Perimeters."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief': ('List the effective dry-run configuration across all Service '
              'Perimeters.'),
    'DESCRIPTION':
        ('By default, only the Service Perimeter name, title, type and the '
         'dry-run mode configuration (as `spec`) is displayed.\n\nNote: For '
         'Service Perimeters without an explicit dry-run mode configuration, '
         'the enforcement mode configuration is used as the dry-run mode '
         'configuration, resulting in no audit logs being generated.'),
    'EXAMPLES':
        ('To list the dry-run mode configuration across all Service '
         'Perimeter:\n\n  $ {command}\n\nOutput:\n\n  name: perimeter_1*\n  '
         'spec:\n    resources:\n    - projects/123\n    - projects/456\n    '
         'restrictedServices:\n    - storage.googleapis.com\n  title: Perimeter'
         ' 1\n  ---\n  name: perimeter_2\n  spec:\n    resources:\n    - '
         'projects/789\n    restrictedServices:\n    - '
         'bigquery.googleapis.com\n    vpcAccessibleServices:\n      '
         'allowedServices:\n      - bigquery.googleapis.com\n      '
         'enableRestriction: true\n  title: Perimeter 2')
}

ListPerimeterDryRunAlpha.detailed_help = detailed_help
ListPerimeterDryRun.detailed_help = detailed_help
