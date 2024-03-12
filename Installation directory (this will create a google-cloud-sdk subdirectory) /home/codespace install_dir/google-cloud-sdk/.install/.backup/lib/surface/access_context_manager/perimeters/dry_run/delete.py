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
"""`gcloud access-context-manager perimeters dry-run delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class DeletePerimeterDryRun(base.UpdateCommand):
  """Marks the Service Perimeter for deletion in the dry-run mode."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to delete')
    parser.add_argument(
        '--async',
        action='store_true',
        help="""Return immediately, without waiting for the operation in
                progress to complete.""")

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    return client.UnsetSpec(perimeter_ref, use_explicit_dry_run_spec=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeletePerimeterDryRunAlpha(DeletePerimeterDryRun):
  """Marks the Service Perimeter for deletion in the dry-run mode."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief':
        'Mark the Service Perimeter as deleted in the dry-run mode.',
    'DESCRIPTION':
        ('When this command completed successfully, the affected Service '
         'Perimeter will be considered to have been deleted in the dry-run '
         'mode, but the enforcement mode configuration will be left untouched.'
        ),
    'EXAMPLES':
        ('To mark the Service Perimeter as deleted in the dry-run mode:\n\n'
         '  $ {command} my-perimeter')
}

DeletePerimeterDryRunAlpha.detailed_help = detailed_help
DeletePerimeterDryRun.detailed_help = detailed_help
