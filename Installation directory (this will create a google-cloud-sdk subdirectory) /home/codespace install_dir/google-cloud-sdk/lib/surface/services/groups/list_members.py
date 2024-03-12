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
"""services groups list members command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'
_SERVICE_RESOURCE = 'services/{}'
_GROUP_RESOURCE = 'groups/{}'


# TODO(b/321801975) make command public after suv2 launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListGroupMembers(base.ListCommand):
  """List members of a specific service and group.

  List members of a specific service and group.

  ## EXAMPLES

   List members of service my-service and group my-group:

   $ {command} my-service my-group

   List members of service my-service and group my-group
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
            name:label=''
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
      resource_name = _FOLDER_RESOURCE.format(args.folder)
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE.format(args.organization)
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE.format(args.project)
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE.format(project)
    response = serviceusage.ListGroupMembersV2Alpha(
        resource_name,
        '{}/{}'.format(
            _SERVICE_RESOURCE.format(args.service),
            _GROUP_RESOURCE.format(args.group),
        ),
        args.page_size,
    )

    group_members = []
    result = collections.namedtuple('ListMembers', ['name'])

    for member_list in response:
      member = member_list.member
      if member.groupName:
        group_members.append(result(member.groupName))
      else:
        group_members.append(result(member.serviceName))

    return group_members
