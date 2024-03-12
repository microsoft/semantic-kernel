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
"""SetIamPolicy command for the Resource Manager - Tag Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class SetIamPolicy(base.Command):
  """Sets IAM policy for a TagKey resource.

    Sets the IAM policy for a TagKey resource given the TagKey's display
    name and parent or the TagKey's numeric id and a file encoded in
    JSON or YAML that contains the IAM policy.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To set the IAM policy for a TagKey with id '123' and IAM policy
          defined in a YAML file '/path/to/my_policy.yaml', run:

            $ {command} tagKeys/123 /path/to/my_policy.yaml

          To set the IAM policy for a tagKey with the short_name 'env' under
          'organization/456' and IAM policy defined in a JSON file
          '/path/to/my_policy.json', run:

            $ {command} 456/env /path/to/my_policy.json
          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)
    arguments.AddPolicyFileArgToParser(parser)

  def Run(self, args):
    service = tags.TagKeysService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagKeys/') == 0:
      tag_key = args.RESOURCE_NAME
    else:
      tag_key = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_KEYS
      ).name

    policy = iam_util.ParsePolicyFile(args.POLICY_FILE, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    set_iam_policy_request = messages.SetIamPolicyRequest(policy=policy)

    request = messages.CloudresourcemanagerTagKeysSetIamPolicyRequest(
        resource=tag_key, setIamPolicyRequest=set_iam_policy_request)
    result = service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(tag_key, 'TagKey')
    return result
