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
"""Set IAM Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class SetIamPolicy(base.Command):
  """Set the IAM policy for an IAP TCP Destination Group resource.

  This command replaces the existing IAM policy for an IAP TCP Destination Group
  resource, given a file encoded in JSON or YAML that contains the IAM policy.
  If the given policy file specifies an "etag" value, then the replacement will
  succeed only if the policy already in place matches that etag. (An etag
  obtained via $ {parent_command} get-iam-policy will prevent the replacement if
  the policy for the resource has been subsequently updated.) A policy file that
  does not contain an etag value will replace any existing policy for the
  resource.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To set the IAM policy for the TCP Destination Group resource within
          the active project in the group 'my-group' located in the region
          'us-west1', run:

            $ {command} POLICY_FILE  --dest-group=='my-group' --region='us-west1'

          To set the IAM policy for the TCP Destination Group resource within
          project PROJECT_ID in the group 'my-group' located in the region
          'us-west1', run:

            $ {command} POLICY_FILE --project=PROJECT_ID --dest-group=='my-group'
              --region='us-west1'
  """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIAMPolicyFileArg(parser)
    iap_util.AddIamDestGroupArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    iap_iam_ref = iap_util.ParseIapDestGroupResource(self.ReleaseTrack(), args)
    return iap_iam_ref.SetIamPolicy(args.policy_file)
