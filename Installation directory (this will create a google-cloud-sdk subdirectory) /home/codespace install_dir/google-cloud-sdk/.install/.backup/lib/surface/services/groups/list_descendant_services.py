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
"""services groups list descendant services command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/%s'
_FOLDER_RESOURCE = 'folders/%s'
_ORGANIZATION_RESOURCE = 'organizations/%s'
_SERVICE_RESOURCE = 'services/%s'
_GROUP_RESOURCE = 'groups/%s'


# TODO(b/321801975) make command public after suv2alpha launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListDescendantServices(base.ListCommand):
  """List descendant services of a specific service and group.

  List descendant services of a specific service and group.

  ## EXAMPLES

   List descendant services of service my-service and group my-group:

   $ {command} my-service my-group

   List descendant services of service my-service and group my-group
   for a specific project '12345678':

    $ {command} my-service my-group --project=12345678
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('service', help='Name of the service.')
    parser.add_argument(
        'group', help='Service group name, for example "dependencies".'
    )
    common_flags.add_resource_args(parser)

    base.PAGE_SIZE_FLAG.SetDefault(parser, 50)

    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
          table(
            serviceName:label=''
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Resource name and its parent name.
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
    response = serviceusage.ListDescendantServices(
        resource_name,
        '{}/{}'.format(
            _SERVICE_RESOURCE % args.service, _GROUP_RESOURCE % args.group
        ),
    )
    return response
