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
"""The command group for Target Projects."""

from googlecloudsdk.calliope import base


# We could have multiple tracks here, e.g.
#   @base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class TargetProjects(base.Group):
  """Manage Target Projects.

  target-projects sub-group is used to manage Target Project resources of the
  Migrate to Virtual Machines service.
  Target projects are defined for each customer project in the global location.
  A Target Project could be used as the target project of various migration
  commands.
  VM Migration API must be enabled in your project.

  ## List Target Projects
  gcloud alpha migration vms target-projects list
  """
