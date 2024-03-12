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
"""services policies test-enabled command."""
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/%s'
_FOLDER_RESOURCE = 'folders/%s'
_ORGANIZATION_RESOURCE = 'organizations/%s'
_SERVICE = 'services/%s'


# TODO(b/321801975) make command public after suv2 launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class TestEnabled(base.Command):
  """Test a value against the result of merging consumer policies in the resource hierarchy.

  Test a value against the result of merging consumer policies in the resource
  hierarchy.

  ## EXAMPLES

  Test for service my-service for current project:

    $ {command} my-service

  Test for service my-service for project `my-project`:

    $ {command} my-service --project=my-project
  """

  @staticmethod
  def Args(parser):
    common_flags.add_resource_args(parser)
    parser.add_argument('service', help='Name of the service.')

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The enablement of the given service.
    """
    if args.IsSpecified('folder'):
      resource_name = _FOLDER_RESOURCE % args.folder
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE % args.organization
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE % args.project
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE % project

    response = serviceusage.TestEnabled(resource_name, _SERVICE % args.service)

    # If enableRules is empty that means service is not enabled.
    if response.enableRules:
      log.status.Print(
          'service %s is ENABLED for resource %s\n'
          % (
              args.service,
              resource_name,
          )
      )
      return response

    else:
      log.status.Print(
          'service %s is NOT ENABLED for resource %s'
          % (
              args.service,
              resource_name,
          )
      )
