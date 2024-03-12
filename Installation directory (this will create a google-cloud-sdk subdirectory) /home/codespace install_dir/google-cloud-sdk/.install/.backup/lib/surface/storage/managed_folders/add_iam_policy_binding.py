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
"""Implementation of managed-folders add-iam-policy-binding command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import iam_command_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import set_iam_policy_task


class AddIamPolicyBinding(base.Command):
  """Add an IAM policy binding to a managed folder."""

  detailed_help = {
      'DESCRIPTION': """
      Add an IAM policy binding to a managed folder. For more information, see [Cloud
      Identity and Access
      Management](https://cloud.google.com/storage/docs/access-control/iam).
      """,
      'EXAMPLES': """
      To grant a single role to a single principal for a managed folder `managed-folder` in a bucket `bucket`:

        $ {command} gs://bucket/managed-folder --member=user:john.doe@example.com --role=roles/storage.objectCreator

      To make objects in `gs://bucket/managed-folder` publicly readable:

        $ {command} gs://bucket/managed-folder --member=allUsers --role=roles/storage.objectViewer

      To specify a custom role for a principal on `gs://bucket/managed-folder`:

        $ {command} gs://bucket/managed-folder --member=user:john.doe@example.com --role=roles/customRoleName
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', help='URL of the managed folder to add IAM policy binding to.'
    )
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)

  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_managed_folder(args.command_path, url)

    api_client = api_factory.get_api(url.scheme)
    messages = apis.GetMessagesModule('storage', 'v1')

    try:
      policy = api_client.get_managed_folder_iam_policy(
          url.bucket_name, url.object_name
      )
    except api_errors.NotFoundError:
      api_client.create_managed_folder(url.bucket_name, url.object_name)
      policy = messages.Policy()

    return iam_command_util.add_iam_binding_to_resource(
        args,
        url,
        messages,
        policy,
        set_iam_policy_task.SetManagedFolderIamPolicyTask,
    )
