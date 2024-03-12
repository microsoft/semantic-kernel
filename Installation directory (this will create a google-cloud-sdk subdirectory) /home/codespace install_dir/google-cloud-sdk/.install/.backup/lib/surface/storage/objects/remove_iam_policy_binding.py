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
"""Implementation of objects remove-iam-policy-binding command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import iam_command_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import set_iam_policy_task


@base.Hidden
class RemoveIamPolicyBinding(base.Command):
  """Remove an IAM policy binding from an object."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* behaves similarly to
      *{parent_command} remove-object-acl-grant*, but uses the IAM policy
      binding syntax.
      """,
      'EXAMPLES':
          """
      To remove access equivalent to the IAM role of
      roles/storage.legacyObjectOwner for the user john.doe@example.com on
      OBJECT in BUCKET:

        $ {command} gs://BUCKET/OBJECT --member=user:john.doe@example.com --role=roles/storage.legacyObjectOwner
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', help='URL of object to remove IAM policy binding from.')
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)

  def Run(self, args):
    url_object = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_cloud_object(args.command_path, url_object)
    errors_util.raise_error_if_not_gcs(args.command_path, url_object)

    client = api_factory.get_api(url_object.scheme)
    policy = client.get_object_iam_policy(url_object.bucket_name,
                                          url_object.object_name,
                                          url_object.generation)

    return iam_command_util.remove_iam_binding_from_resource(
        args, url_object, policy, set_iam_policy_task.SetObjectIamPolicyTask
    )
