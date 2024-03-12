# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""The command group for the projects CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Projects(base.Group):
  """Create and manage project access policies.

  The {command} group lets you create and manage IAM policies for projects on
  the Google Cloud Platform. Resources are organized hierarchically and assigned
  to a particular project.  A Project resource is required to use Google Cloud
  Platform, and forms the basis for creating, enabling and using all Cloud
  Platform services, managing APIs, enabling billing, adding and removing
  collaborators, and managing permissions.

  More information on the Cloud Platform Resource Hierarchy and the project
  resource can be found here:
  https://cloud.google.com/resource-manager/docs/creating-managing-organization
  and detailed documentation on creating and managing projects can be found
  here:
  https://cloud.google.com/resource-manager/docs/creating-managing-projects
  """

  category = base.MANAGEMENT_TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    parser.display_info.AddUriFunc(util.ProjectsUriFunc)

  def Filter(self, context, args):
    del context, args
    # Don't ever take this off. Use gcloud quota for projects operations so
    # you can create a project before you have a project.
    base.DisableUserProjectQuota()
