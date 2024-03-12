# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of managed-folders remove-iam-policy-binding command."""

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


class RemoveIamPolicyBinding(base.Command):
  """Remove an IAM policy binding from a managed folder."""

  detailed_help = {
      'DESCRIPTION': """
      Remove a policy binding from the IAM policy of a managed folder, given a managed folder
      URL and the binding. For more information, see [Cloud
      Identity and Access
      Management](https://cloud.google.com/storage/docs/access-control/iam).
      """,
      'EXAMPLES': """
      To remove an IAM policy binding from the role of
      roles/storage.objectCreator for the user john.doe@example.com on a managed folder `managed-folder` in a bucket `bucket`:

        $ {command} gs://bucket/managed-folder --member=user:john.doe@example.com --role=roles/storage.objectCreator
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', help='URL of managed folder to remove IAM policy binding from.'
    )
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)

  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_managed_folder(args.command_path, url)
    policy = api_factory.get_api(url.scheme).get_managed_folder_iam_policy(
        url.bucket_name, url.object_name
    )
    return iam_command_util.remove_iam_binding_from_resource(
        args,
        url,
        policy,
        set_iam_policy_task.SetManagedFolderIamPolicyTask,
    )
