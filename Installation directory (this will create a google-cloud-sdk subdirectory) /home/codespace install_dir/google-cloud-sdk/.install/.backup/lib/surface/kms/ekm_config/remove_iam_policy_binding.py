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
"""Remove IAM Policy Binding for EkmConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.kms import resource_args


class RemoveIamPolicyBinding(base.Command):
  """Remove IAM policy binding from an EkmConfig.

  Removes a policy binding from the IAM policy of a kms EkmConfig. A binding
  consists of at
  least one member, a role, and an optional condition.

  ## EXAMPLES
  To remove an IAM policy binding for the role of 'roles/editor' for the user
  'test-user@gmail.com' on the EkmConfig with location us-central1, run:

    $ {command} --location='us-central1' --member='user:test-user@gmail.com'
    --role='roles/editor'

  To remove an IAM policy binding with a condition of
  expression='request.time < timestamp("2023-01-01T00:00:00Z")',
  title='expires_end_of_2022',
  and description='Expires at midnight on 2022-12-31' for the role of
  'roles/editor'
  for the user 'test-user@gmail.com' on the EkmConfig with location us-central1,
  run:

    $ {command} --location='us-central1' --member='user:test-user@gmail.com'
    --role='roles/editor' --condition='expression=request.time <
    timestamp("2023-01-01T00:00:00Z"),title=expires_end_of_2022,description=Expires
    at midnight on 2022-12-31'

  To remove all IAM policy bindings regardless of the condition for the role of
  'roles/editor' and for the user 'test-user@gmail.com' on the EkmConfig with
  location us-central1, run:

    $ {command} laplace --location='us-central1'
    --member='user:test-user@gmail.com' --role='roles/editor' --all

  See https://cloud.google.com/iam/docs/managing-policies for details of
  policy role and member types.
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    ekm_config_name = 'projects/{0}/locations/{1}/ekmConfig'.format(
        location_ref.projectsId, location_ref.locationsId)
    result = iam.RemovePolicyBindingFromEkmConfig(ekm_config_name, args.member,
                                                  args.role)
    iam_util.LogSetIamPolicy(ekm_config_name, 'EkmConfig')
    return result
