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
"""AddIamPolicyBinding command for the Resource Manager - Tag Keys CLI."""

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
class AddIamPolicyBinding(base.Command):
  """Adds a policy binding to the IAM policy of a TagKey.

     Adds the IAM policy binding for a TagKey resource given the binding
     and an identifier for the TagKey. The identifier can be the TagKey's
     parent/short name or the TagKey's ID in the form:
     tagKeys/{numeric_id}.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To add an IAM policy binding for the role of 'roles/editor' for the
          user 'test-user@gmail.com' on the Tag Key 'tagKeys/123', run:

            $ {command} tagKeys/123 --member='user:test-user@gmail.com' --role='roles/editor'

          To add an IAM policy binding for a Tag Key with the name 'env' under
          'organization/456' for the role of 'roles/resourcemanager.tagUser' for
          the user 'test-user@gmail.com', run:

            $ {command} 456/env --member='user:test-user@gmail.com' --role='roles/resourcemanager.tagUser'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.

          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)

  # Allow for retries due to etag-based optimistic concurrency control
  @http_retry.RetryOnHttpStatus(six.moves.http_client.CONFLICT)
  def Run(self, args):
    service = tags.TagKeysService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagKeys/') == 0:
      tag_key = args.RESOURCE_NAME
    else:
      tag_key = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_KEYS
      ).name

    get_iam_policy_req = (
        messages.CloudresourcemanagerTagKeysGetIamPolicyRequest(
            resource=tag_key))
    policy = service.GetIamPolicy(get_iam_policy_req)
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    iam_util.AddBindingToIamPolicyWithCondition(messages.Binding, messages.Expr,
                                                policy, args.member, args.role,
                                                condition)

    set_iam_policy_request = messages.SetIamPolicyRequest(policy=policy)
    request = messages.CloudresourcemanagerTagKeysSetIamPolicyRequest(
        resource=tag_key, setIamPolicyRequest=set_iam_policy_request)
    result = service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(tag_key, 'TagKey')
    return result
