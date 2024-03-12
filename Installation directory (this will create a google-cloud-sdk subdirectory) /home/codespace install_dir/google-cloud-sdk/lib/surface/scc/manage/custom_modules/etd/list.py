# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to list details of resident and inherited Event Threat Detection Custom Modules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc.manage.etd import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.manage import flags
from googlecloudsdk.command_lib.scc.manage import parsing


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List details of resident and inherited Event Threat Detection Custom Modules.

  List the details of the resident and inherited Event Threat Detection
  custom modules for the specified folder or project. For an organization, this
  command lists only the custom modules that are created at the organization
  level. Custom modules created in child folders or projects are not included in
  the list. To list the resident custom modules and the modules that are created
  in child folders or projects, use `gcloud scc manage custom-modules etd
  list-descendant`.

  ## EXAMPLES

  To list resident and inherited Event Threat Detection custom modules for
  organization `123`, run:

  $ {command} --organization=organizations/123

  To list resident and inherited Event Threat Detection custom modules for
  folder `456`, run:

  $ {command} --folder=folders/456

  To list resident and inherited Event Threat Detection custom modules for
  project `789`, run:

  $ {command} --project=projects/789
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    flags.CreateParentFlag(required=True).AddToParser(parser)

  def Run(self, args):
    parent = parsing.GetParentResourceNameFromArgs(args)
    page_size = args.page_size

    client = clients.ETDCustomModuleClient()

    return client.List(
        page_size=page_size,
        parent=parent,
        limit=args.limit,
    )
