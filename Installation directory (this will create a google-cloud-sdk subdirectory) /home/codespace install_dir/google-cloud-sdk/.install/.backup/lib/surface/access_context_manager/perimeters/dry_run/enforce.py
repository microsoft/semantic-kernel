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
"""`gcloud access-context-manager perimeters dry-run enforce` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class EnforcePerimeterDryRun(base.UpdateCommand):
  """Enforces a Service Perimeter's dry-run configuration."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to reset')
    parser.add_argument(
        '--async',
        action='store_true',
        help="""Return immediately, without waiting for the operation in
            progress to complete.""")

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    return client.EnforceDryRunConfig(perimeter_ref)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnforcePerimeterDryRunAlpha(EnforcePerimeterDryRun):
  """Enforces a Service Perimeter's dry-run configuration."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief':
        'Enforces a Service Perimeter\'s dry-run configuration.',
    'DESCRIPTION':
        """\
        Copies a Service Perimeter\'s dry-run mode configuration to its
        enforcement mode configuration and unsets the explicit dry-run spec.
        After this operation succeeds, the Service Perimeter will not have
        an explicit dry-run mode configuration, and, instead, the previous
        dry-run mode configuration will become the enforcement mode
        configuration. The operation will not be performed if there is no
        explicit dry-run mode configuration or if the dry-run mode
        configuration is incompatible with the overall enforcement mode VPC
        Service Controls policy.""",
    'EXAMPLES':
        """\
        To enforce the dry-run mode configuration for a Service Perimeter:\n\n
          $ {command} my-perimeter"""
}

EnforcePerimeterDryRunAlpha.detailed_help = detailed_help
EnforcePerimeterDryRun.detailed_help = detailed_help
