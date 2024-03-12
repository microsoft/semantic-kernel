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
"""Implementation of objects set-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage.gcs_json import metadata_field_converters
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import iam_command_util
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import set_iam_policy_task


def _set_iam_policy_task_iterator(url_strings, recurse, object_state, policy):
  """Generates SetIamPolicyTask's for execution."""
  if recurse:
    recursion_requested = name_expansion.RecursionSetting.YES
  else:
    recursion_requested = name_expansion.RecursionSetting.NO_WITH_WARNING

  for name_expansion_result in name_expansion.NameExpansionIterator(
      url_strings,
      fields_scope=cloud_api.FieldsScope.SHORT,
      object_state=object_state,
      recursion_requested=recursion_requested,
  ):
    yield set_iam_policy_task.SetObjectIamPolicyTask(
        name_expansion_result.resource.storage_url, policy
    )


@base.Hidden
class SetIamPolicy(base.Command):
  """Set access policy for an object."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* behaves similarly to *{parent_command} set-object-acl*, but
      uses the IAM policy binding syntax.
      """,
      'EXAMPLES':
          """
      To set the access policy for OBJECT on BUCKET to the policy defined in
      POLICY-FILE run:

        $ {command} gs://BUCKET/OBJECT POLICY-FILE

      To set the IAM policy in POLICY-FILE on all objects in all buckets
      beginning with "b":

        $ {command} -r gs://b* POLICY-FILE
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls',
        nargs='+',
        help='The URLs for objects whose access policy is being replaced.')
    iam_util.AddArgForPolicyFile(parser)
    parser.add_argument(
        '--all-versions',
        action='store_true',
        help='Update the IAM policies of all versions of an object in a'
        ' versioned bucket.')
    parser.add_argument(
        '-e',
        '--etag',
        help='Custom etag to set on IAM policy. API will reject etags that do'
        ' not match this value, making it useful as a precondition during'
        ' concurrent operations.')
    parser.add_argument(
        '-R',
        '-r',
        '--recursive',
        action='store_true',
        help='Recursively set the IAM policies of the contents of any'
        ' directories that match the source path expression.')
    flags.add_continue_on_error_flag(parser)

  def Run(self, args):
    for url_string in args.urls:
      url = storage_url.storage_url_from_string(url_string)
      if not args.recursive:
        errors_util.raise_error_if_not_cloud_object(args.command_path, url)
      errors_util.raise_error_if_not_gcs(args.command_path, url)

    policy = metadata_field_converters.process_iam_file(
        args.policy_file, custom_etag=args.etag)
    exit_code, output = iam_command_util.execute_set_iam_task_iterator(
        _set_iam_policy_task_iterator(
            args.urls,
            args.recursive,
            flags.get_object_state_from_flags(args),
            policy,
        ),
        args.continue_on_error,
    )

    self.exit_code = exit_code
    return output
