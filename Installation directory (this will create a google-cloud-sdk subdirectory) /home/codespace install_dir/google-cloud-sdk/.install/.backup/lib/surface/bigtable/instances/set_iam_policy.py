# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command for bigtable instances set-iam-policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.command_lib.bigtable import iam
from googlecloudsdk.command_lib.iam import iam_util


class SetIamPolicy(base.Command):
  """Set the IAM policy for a Cloud Bigtable instance."""

  detailed_help = iam_util.GetDetailedHelpForSetIamPolicy(
      'instance', example_id='my-instance-id', use_an=True)

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddInstanceResourceArg(
        parser, 'to set the IAM policy for', positional=True)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A IAM policy message.
    """
    instance_ref = util.GetInstanceRef(args.instance)
    result = iam.SetInstanceIamPolicy(instance_ref, args.policy_file)
    iam_util.LogSetIamPolicy(instance_ref.Name(), 'instance')
    return result
