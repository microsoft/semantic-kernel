# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Removes an invoker binding from the IAM policy of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util as api_util_v1
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import util
from googlecloudsdk.command_lib.functions.v2.remove_invoker_policy_binding import command as command_v2
from googlecloudsdk.command_lib.iam import iam_util


_DETAILED_HELP = {
    'DESCRIPTION': """\
      Removes the invoker role IAM policy binding that allows the specified
      member to invoke the specified function.

      For Cloud Functions (1st gen), this removes the Cloud Functions Invoker
      binding from the IAM policy of the specified function.

      For Cloud Functions (2nd gen), this removes the Cloud Run Invoker binding
      from the IAM policy of the specified function's underlying Cloud Run
      service.
      """,
    'EXAMPLES': """\
          To remove the invoker role policy binding for `FUNCTION-1` for member
          `MEMBER-1` run:

            $ {command} FUNCTION-1 --member=MEMBER-1
          """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RemoveInvokerPolicyBinding(util.FunctionResourceCommand):
  """Removes an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions 2nd gen only.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to remove the invoker binding from')
    flags.AddGen2Flag(parser, 'to remove the invoker binding from', hidden=True)
    iam_util.AddMemberFlag(parser, 'to remove from the IAM policy', False)

  def _RunV1(self, args: parser_extensions.Namespace):
    return api_util_v1.RemoveFunctionIamPolicyBindingIfFound(
        args.CONCEPTS.name.Parse().RelativeName(),
        member=args.member,
        role='roles/cloudfunctions.invoker',
    )

  def _RunV2(self, args: parser_extensions.Namespace):
    return command_v2.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RemoveInvokerPolicyBindingBeta(RemoveInvokerPolicyBinding):
  """Removes an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions 2nd gen only.
  """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveInvokerPolicyBindingAlpha(RemoveInvokerPolicyBindingBeta):
  """Removes an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions 2nd gen only.
  """
