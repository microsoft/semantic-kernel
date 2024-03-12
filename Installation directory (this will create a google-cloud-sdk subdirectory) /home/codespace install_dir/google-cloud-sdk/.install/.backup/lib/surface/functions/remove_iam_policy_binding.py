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
"""Removes an IAM policy binding from a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import util
from googlecloudsdk.command_lib.functions.v1.remove_iam_policy_binding import command as command_v1
from googlecloudsdk.command_lib.functions.v2.remove_iam_policy_binding import command as command_v2
from googlecloudsdk.command_lib.iam import iam_util

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
          To remove the iam policy binding for `FUNCTION-1` from role
          `ROLE-1` for member `MEMBER-1` run:

            $ {command} FUNCTION-1 --member=MEMBER-1 --role=ROLE-1
          """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RemoveIamPolicyBinding(util.FunctionResourceCommand):
  """Removes an IAM policy binding from a Google Cloud Function."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to remove IAM policy binding from')
    iam_util.AddArgsForRemoveIamPolicyBinding(parser)
    flags.AddGen2Flag(parser, hidden=True)

  def _RunV1(self, args):
    return command_v1.Run(args)

  def _RunV2(self, args):
    return command_v2.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RemoveIamPolicyBindingBeta(RemoveIamPolicyBinding):
  """Removes an IAM policy binding from a Google Cloud Function."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveIamPolicyBindingAlpha(RemoveIamPolicyBindingBeta):
  """Removes an IAM policy binding from a Google Cloud Function."""
