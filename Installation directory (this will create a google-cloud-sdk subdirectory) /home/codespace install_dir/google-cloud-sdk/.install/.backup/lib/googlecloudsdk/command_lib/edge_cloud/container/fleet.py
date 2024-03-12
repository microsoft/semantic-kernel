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
"""Utils for GKE Hub memberships commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.command_lib.run import flags


def SetFleetProjectPath(ref, args, request):
  """Sets the cluster.fleet.project field with a relative resource path.

  Args:
    ref: reference to the projectsId object.
    args: command line arguments.
    request: API request to be issued
  """
  release_track = args.calliope_command.ReleaseTrack()
  msgs = util.GetMessagesModule(release_track)
  if flags.FlagIsExplicitlySet(args, 'fleet_project'):
    request.cluster.fleet = msgs.Fleet()
    request.cluster.fleet.project = 'projects/' + args.fleet_project
  else:
    request.cluster.fleet = msgs.Fleet()
    request.cluster.fleet.project = 'projects/' + ref.projectsId
