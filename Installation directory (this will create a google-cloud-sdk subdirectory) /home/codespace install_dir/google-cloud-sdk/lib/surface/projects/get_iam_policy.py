# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command to get IAM policy for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class GetIamPolicy(base.ListCommand):
  """Get IAM policy for a project.

  Gets the IAM policy for a project, given a project ID.

  ## EXAMPLES

  The following command prints the IAM policy for a project with the ID
  `example-project-id-1`:

    $ {command} example-project-id-1
  """

  @staticmethod
  def Args(parser):
    flags.GetProjectIDNumberFlag('get IAM policy for').AddToParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    return projects_api.GetIamPolicy(project_ref)
