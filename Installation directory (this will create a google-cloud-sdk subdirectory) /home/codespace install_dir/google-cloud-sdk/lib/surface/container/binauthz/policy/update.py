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
"""Update policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import parsing


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  # pylint: disable=line-too-long
  """Update a Binary Authorization platform policy.

  ## EXAMPLES

  To update an existing policy using its resource name:

    $ {command} projects/my_proj/platforms/gke/policies/policy1 --policy-file=policy1.json

  To update the same policy using flags:

    $ {command} policy1 --platform=gke --project=my_proj --policy-file=policy1.json
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    flags.AddPlatformPolicyResourceArg(parser, 'to update')
    parser.add_argument(
        '--policy-file',
        required=True,
        help='The JSON or YAML file containing the new policy.')
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    # The API is only available in v1.
    messages = apis.GetMessagesModule('v1')
    policy_ref = args.CONCEPTS.policy_resource_name.Parse().RelativeName()
    # Load the policy file into a Python dict.
    policy_obj = parsing.LoadResourceFile(args.policy_file)
    # Decode the dict into a PlatformPolicy message, allowing DecodeErrors to
    # bubble up to the user if they are raised.
    policy = messages_util.DictToMessageWithErrorCheck(policy_obj,
                                                       messages.PlatformPolicy)
    return platform_policy.Client('v1').Update(policy_ref, policy)
