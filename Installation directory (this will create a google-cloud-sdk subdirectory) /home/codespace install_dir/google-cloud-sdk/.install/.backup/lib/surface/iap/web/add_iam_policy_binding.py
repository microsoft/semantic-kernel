# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Add IAM Policy Binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to an IAP IAM resource.

  Adds a policy binding to the IAM policy of an IAP IAM resource. One binding
  consists of a member, a role, and an optional condition.
  See $ {parent_command} get-iam-policy for examples of how to specify an IAP
  IAM resource.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          See $ {parent_command} get-iam-policy for examples of how to specify
          an IAP IAM resource.

          To add an IAM policy binding for the role of 'roles/editor' for the
          user 'test-user@gmail.com' on IAP IAM resource IAP_IAM_RESOURCE,
          run:

            $ {command} --resource-type=IAP_IAM_RESOURCE --member='user:test-user@gmail.com'
                --role='roles/editor'

          To add an IAM policy binding for the role of 'roles/editor' for all
          authenticated users on IAP IAM resource IAP_IAM_RESOURCE,
          run:

            $ {command} --resource-type=IAP_IAM_RESOURCE --member='allAuthenticatedUsers'
                --role='roles/editor'

          To add an IAM policy binding which expires at the end of the year 2018
          for the role of 'roles/browser' and the user 'test-user@gmail.com' on
          IAP IAM resource IAP_IAM_RESOURCE, run:

            $ {command} --resource-type=IAP_IAM_RESOURCE --member='user:test-user@gmail.com'
                --role='roles/browser' --condition='expression=request.time <
                timestamp("2019-01-01T00:00:00Z"),title=expires_end_of_2018,
                description=Expires at midnight on 2018-12-31'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.
  """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIapIamResourceArgs(parser)
    iap_util.AddAddIamPolicyBindingArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    iap_iam_ref = iap_util.ParseIapIamResource(self.ReleaseTrack(), args)
    return iap_iam_ref.AddIamPolicyBinding(args.member, args.role, condition)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBindingALPHA(AddIamPolicyBinding):
  """Add IAM policy binding to an IAP IAM resource.

  Adds a policy binding to the IAM policy of an IAP IAM resource. One binding
  consists of a member, a role, and an optional condition.
  See $ {parent_command} get-iam-policy for examples of how to specify an IAP
  IAM resource.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIapIamResourceArgs(parser, use_region_arg=True)
    iap_util.AddAddIamPolicyBindingArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)
