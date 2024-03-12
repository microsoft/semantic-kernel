# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to show fleet namespaces in a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import deprecation_utils
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.core import properties


@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='447.0.0',
    remove=True,
    alt_command='gcloud fleet scopes namespaces list',
)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List fleet namespaces in a project.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The user does not have access to the project specified.

  ## EXAMPLES

  The following command lists namespaces in the active project:

    $ {command}

  The following command lists namespaces in project `PROJECT_ID`:

    $ {command} --project=PROJECT_ID
  """

  @staticmethod
  def Args(parser):
    # Table formatting
    parser.display_info.AddFormat(util.NS_LIST_FORMAT)

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get()
    return fleetclient.ListNamespaces(project)
