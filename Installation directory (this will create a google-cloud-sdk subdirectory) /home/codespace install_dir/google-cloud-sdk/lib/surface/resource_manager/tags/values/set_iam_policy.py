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
"""SetIamPolicy command for the Resource Manager - Tag Values CLI."""

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
  """Sets IAM policy for a TagValue resource.

    Sets the IAM policy for a TagValue resource given the TagValue's short name
    name and parent or the TagValue's numeric id and a file encoded in
    JSON or YAML that contains the IAM policy.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To set the IAM policy for a TagValue with id '111' and IAM policy
          defined in a YAML file '/path/to/my_policy.yaml', run:

            $ {command} tagValues/111 /path/to/my_policy.yaml

          To set the IAM policy for a tagValue with the short_name 'dev' under
          'organization/456' and tag key short name 'env' and IAM policy
          defined in a JSON file '/path/to/my_policy.json', run:

            $ {command} 456/env/dev /path/to/my_policy.json
          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)
    arguments.AddPolicyFileArgToParser(parser)

  def Run(self, args):
    service = tags.TagValuesService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagValues/') == 0:
      tag_value = args.RESOURCE_NAME
    else:
      tag_value = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_VALUES
      ).name

    policy = iam_util.ParsePolicyFile(args.POLICY_FILE, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    set_iam_policy_request = messages.SetIamPolicyRequest(policy=policy)

    request = messages.CloudresourcemanagerTagValuesSetIamPolicyRequest(
        resource=tag_value, setIamPolicyRequest=set_iam_policy_request)
    result = service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(tag_value, 'TagValue')
    return result
