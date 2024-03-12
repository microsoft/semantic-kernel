# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to get IAM policy for a resource and its ancestors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import policies_flags
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util


class GetIamPolicy(base.ListCommand):
  """Get IAM policies for a project and its ancestors.

  Get IAM policies for a project and its ancestors, given a project ID.

  ## EXAMPLES

  To get IAM policies for project `example-project-id-1` and its ancestors, run:

    $ {command} example-project-id-1
  """

  @staticmethod
  def Args(parser):
    flags.GetProjectResourceArg('get IAM policy for').AddToParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    policies_flags.AddIncludeDenyFlag(parser)

  def Run(self, args):
    return command_lib_util.GetIamPolicyWithAncestors(args.project_id,
                                                      args.include_deny,
                                                      self.ReleaseTrack())
