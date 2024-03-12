# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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

# TODO: b/300099033 - Capitalize and turn into a sentence.
"""services policies get-effective-policy command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'


# TODO: b/321801975 - Make command public after suv2 launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetEffectivePolicy(base.Command):
  """Get effective policy for a project, folder or organization.

  Get effective policy for a project, folder or organization.

  ## EXAMPLES

   Get effective policy for the current project:

   $ {command}

   Get effective policy for project `my-project`:

   $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--view',
        help=(
            'The view of the effective policy. BASIC includes basic metadata'
            ' about the effective policy. FULL includes every information'
            ' related to effective policy.'
        ),
        default='BASIC',
    )
    common_flags.add_resource_args(parser)

    parser.display_info.AddFormat("""
          table(
            EnabledService:label=EnabledService:sort=1,
            EnabledPolicies:label=EnabledPolicies
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Effective Policy.
    """

    if args.view not in ('BASIC', 'FULL'):
      raise exceptions.ConfigError(
          'Invalid view. Please provide a valid view. Excepted view : BASIC,'
          ' FULL'
      )
    if args.IsSpecified('folder'):
      resource_name = _FOLDER_RESOURCE.format(args.folder)
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE.format(args.organization)
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE.format(args.project)
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE.format(project)

    response = serviceusage.GetEffectivePolicyV2Alpha(
        resource_name + '/effectivePolicy', args.view
    )

    log.status.Print('EnabledRules:')
    for enable_rule in response.enableRules:
      log.status.Print(' Services:')
      for service in enable_rule.services:
        log.status.Print('  - %s' % service)

    if args.view == 'FULL':
      log.status.Print('\nMetadata of effective policy:')
      result = []

      resources = collections.namedtuple(
          'serviceSources', ['EnabledService', 'EnabledPolicies']
      )

      for metadata in response.enableRuleMetadata:
        for values in metadata.serviceSources.additionalProperties:
          result.append(resources(values.key, values.value.policies))
      return result
