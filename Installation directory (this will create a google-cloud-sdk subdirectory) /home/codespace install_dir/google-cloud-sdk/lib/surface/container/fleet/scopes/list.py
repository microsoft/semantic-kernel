# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to show fleet scopes in a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List fleet scopes in a project.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The user does not have access to the project specified.

  ## EXAMPLES

  The following command lists scopes in the active project:

    $ {command}

  The following command lists scopes in project `PROJECT_ID`:

    $ {command} --project=PROJECT_ID
  """

  @staticmethod
  def Args(parser):
    # Table formatting
    parser.display_info.AddFormat(util.SC_LIST_FORMAT)

  def Run(self, args):
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get()
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    # TODO(b/321111171): Use ListPermittedScopes in all release tracks.
    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return fleetclient.ListPermittedScopes(project)
    else:
      return fleetclient.ListScopes(project)
