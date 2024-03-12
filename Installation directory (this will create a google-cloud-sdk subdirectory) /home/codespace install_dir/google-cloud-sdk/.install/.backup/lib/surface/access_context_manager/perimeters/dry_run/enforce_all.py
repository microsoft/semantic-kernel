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
"""`gcloud access-context-manager perimeters dry-run enforce-all` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class EnforceAllPerimeterDryRun(base.UpdateCommand):
  """Enforces the dry-run mode configuration for all Service Perimeters."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--policy',
        metavar='policy',
        default=None,
        help="""The parent Access Policy which owns all Service Perimeters in
                scope for the commit operation.""")
    parser.add_argument(
        '--etag',
        metavar='etag',
        default=None,
        help="""The etag for the version of the Access Policy that this
                operation is to be performed on. If, at the time of the
                operation, the etag for the Access Policy stored in Access
                Context Manager is different from the specified etag, then the
                commit operation will not be performed and the call will fail.
                If etag is not provided, the operation will be performed as if a
                valid etag is provided.""")

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    policy_id = policies.GetDefaultPolicy()
    if args.IsSpecified('policy'):
      policy_id = args.policy

    policy_ref = resources.REGISTRY.Parse(
        policy_id, collection='accesscontextmanager.accessPolicies')

    return client.Commit(policy_ref, args.etag)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnforceAllPerimeterDryRunAlpha(EnforceAllPerimeterDryRun):
  """Enforces the dry-run mode configuration for all Service Perimeters."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief':
        'Enforces the dry-run mode configuration for all Service Perimeters.',
    'DESCRIPTION':
        ('An enforce operation on a Service Perimeter involves copying its '
         'dry-run mode configuration (`spec`) to that Service Perimeter\'s '
         'enforcement mode configration (`status`). This command performs this '
         'operation for *all* Service Perimeters in the user\'s Access '
         'Policy.\n\nNote: Only Service Perimeters with an explicit dry-run '
         'mode configuration are affected by this operation. The overall '
         'operation succeeds once the dry-run configurations of all such '
         'Service Perimeters have been enforced. If the operation fails for '
         'any given Service Perimeter, it will cause the entire operation to'
         ' be aborted.'),
    'EXAMPLES':
        ('To enforce the dry-run mode configurations for all Service Perimeter '
         'in an Access Policy, run the following command:\n\n'
         '  $ {command}')
}

EnforceAllPerimeterDryRunAlpha.detailed_help = detailed_help
EnforceAllPerimeterDryRun.detailed_help = detailed_help
