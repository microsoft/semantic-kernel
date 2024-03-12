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
"""RemoveIamPolicyBinding command for the Resource Manager - Tag Values CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils

import six.moves.http_client


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class RemoveIamPolicyBinding(base.Command):
  """Removes a policy binding from the IAM policy of a TagValue.

     Removes an IAM policy binding for a TagValue resource given the binding
     and an identifier for the TagValue. The identifier can be the TagValue's
     namespaced name in the form
     <parent_namespace>/<tagkey_short_name>/<tagvalue_short_name> or the
     TagValue's ID in the form: tagValues/{numeric_id}.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To remove an IAM policy binding for the role of 'roles/editor' for the
          user 'test-user@gmail.com' on the tagValue 'tagValues/111', run:

            $ {command} tagValues/111 --member='user:test-user@gmail.com' --role='roles/editor'

          To remove an IAM policy binding for a TagValue with the name 'dev'
          under 'organization/456/env' for the role of
          'roles/resourcemanager.tagUser' for the user 'test-user@gmail.com',
          run:

            $ {command} 456/env/dev --member='user:test-user@gmail.com' --role='roles/resourcemanager.tagUser'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.

          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)

  # Allow for retries due to etag-based optimistic concurrency control
  @http_retry.RetryOnHttpStatus(six.moves.http_client.CONFLICT)
  def Run(self, args):
    service = tags.TagValuesService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagValues/') == 0:
      tag_value = args.RESOURCE_NAME
    else:
      tag_value = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_VALUES
      ).name

    get_iam_policy_req = (
        messages.CloudresourcemanagerTagValuesGetIamPolicyRequest(
            resource=tag_value))
    policy = service.GetIamPolicy(get_iam_policy_req)
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    iam_util.RemoveBindingFromIamPolicyWithCondition(policy, args.member,
                                                     args.role, condition,
                                                     args.all)

    set_iam_policy_request = messages.SetIamPolicyRequest(policy=policy)
    request = messages.CloudresourcemanagerTagValuesSetIamPolicyRequest(
        resource=tag_value, setIamPolicyRequest=set_iam_policy_request)
    result = service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(tag_value, 'TagValue')
    return result
