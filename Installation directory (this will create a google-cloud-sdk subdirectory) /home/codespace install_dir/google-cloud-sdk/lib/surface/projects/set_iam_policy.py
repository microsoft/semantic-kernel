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
"""Command to set IAM policy for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class SetIamPolicy(base.Command):
  """Set IAM policy for a project.

  Sets the IAM policy for a project, given a project ID and a file encoded in
  JSON or YAML that contains the IAM policy.

  ## EXAMPLES

  The following command reads an IAM policy defined in a JSON file `policy.json`
  and sets it for a project with the ID `example-project-id-1`:

    $ {command} example-project-id-1 policy.json
  """

  @staticmethod
  def Args(parser):
    flags.GetProjectIDNumberFlag('set IAM policy for').AddToParser(parser)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    results = projects_api.SetIamPolicyFromFile(project_ref, args.policy_file)
    iam_util.LogSetIamPolicy(project_ref.Name(), 'project')
    return results
