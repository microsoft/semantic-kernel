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
"""Create policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import parsing
import six


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Create a Binary Authorization platform policy.

  ## EXAMPLES

  To create a policy for GKE in the current project:

      $ {command} my-policy --platform=gke --policy-file=my_policy.yaml

  To create a policy for GKE in a specific project:

      $ {command} my-policy --platform=gke --project=my-project-id \
        --policy-file=my_policy.yaml

  or

      $ {command} /projects/my-project-id/platforms/gke/policies/my-policy
      \
        --policy-file=my_policy.yaml
  """

  @staticmethod
  def Args(parser):
    flags.AddPlatformPolicyResourceArg(parser, 'to create')
    parser.add_argument(
        '--policy-file',
        required=True,
        help='The JSON or YAML file containing the new policy.')
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    """Runs the command.

    Args:
      args: argparse.Namespace with command-line arguments.

    Returns:
      The policy resource.
    """
    policy_resource_name = args.CONCEPTS.policy_resource_name.Parse()

    # Load the policy file into a Python dict.
    policy_obj = parsing.LoadResourceFile(
        # Avoid 'u' prefix in Python 2 when this file path gets embedded in
        # error messages.
        six.ensure_str(args.policy_file))

    # Decode the dict into a PlatformPolicy message, allowing DecodeErrors to
    # bubble up to the user if they are raised.
    policy = messages_util.DictToMessageWithErrorCheck(
        policy_obj,
        # The API is only available in v1.
        apis.GetMessagesModule('v1').PlatformPolicy)

    return platform_policy.Client('v1').Create(policy_resource_name, policy)
