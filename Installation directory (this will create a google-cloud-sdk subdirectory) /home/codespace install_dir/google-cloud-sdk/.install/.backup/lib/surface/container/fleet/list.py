# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Command to show fleets in an organization or project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api as crm
from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List fleets visible to the user in an organization.

  This command can fail for the following reasons:
  * The org or project specified does not exist.
  * The user does not have access to the project specified.

  ## EXAMPLES

  The following command lists fleets in organization `12345`:

    $ {command} --organization=12345
  """

  @staticmethod
  def Args(parser):
    # Organization flag
    orgflag = base.Argument(
        '--organization',
        metavar='ORGANIZATION_ID',
        help='''ID (number) for the organization to list fleets from. \
If neither --organization nor --project are provided, defaults to the organization of the active project.\
''',
        category=base.COMMONLY_USED_FLAGS)
    orgflag.AddToParser(parser)
    # Table formatting
    parser.display_info.AddFormat(util.LIST_FORMAT)

  def Run(self, args):
    base.EnableUserProjectQuota()
    fleetclient = client.FleetClient(release_track=base.ReleaseTrack.ALPHA)
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get()
    org = args.organization
    # If no args provided, use active project org
    if org is None and args.project is None:
      org = self.GetOrg(project)
    parent = org if org is not None else project
    parenttype = 'organization' if org is not None else 'project'
    log.status.Print('Listing fleets from {0} {1}:'.format(parenttype, parent))
    return fleetclient.ListFleets(project, org)

  def GetOrg(self, project):
    ancestry = crm.GetAncestry(project_id=project)
    for resource in ancestry.ancestor:
      resource_type = resource.resourceId.type
      resource_id = resource.resourceId.id
      # this is the given project
      if resource_type == 'project':
        pass
      if resource_type == 'folder':
        pass
      if resource_type == 'organization':
        return resource_id
