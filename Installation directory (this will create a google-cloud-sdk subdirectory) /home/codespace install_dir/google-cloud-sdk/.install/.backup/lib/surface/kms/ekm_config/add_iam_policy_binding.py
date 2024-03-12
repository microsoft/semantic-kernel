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
"""Add IAM Policy Binding for EkmConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.kms import resource_args


class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to an EkmConfig.

  Adds a policy binding to the IAM policy of a kms EkmConfig. A binding consists
  of at least one member, a role, and an optional condition.

  ## EXAMPLES
  To add an IAM policy binding for the role of 'roles/editor' for the user
  `test-user@gmail.com` on the EkmConfig with location `us-central1`, run:

    $ {command} --location='us-central1' --member='user:test-user@gmail.com'
    --role='roles/editor'

  To add an IAM policy binding which expires at the end of the year 2022 for the
  role of 'roles/editor' and the user `test-user@gmail.com` and location
  `us-central1`, run:

    $ {command} --location='us-central1' --member='user:test-user@gmail.com'
    --role='roles/editor' --condition='expression=request.time <
    timestamp("2023-01-01T00:00:00Z"),title=expires_end_of_2022,description=Expires
    at midnight on 2022-12-31'

  See https://cloud.google.com/iam/docs/managing-policies for details of
  policy role and member types.
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    ekm_config_name = 'projects/{0}/locations/{1}/ekmConfig'.format(
        location_ref.projectsId, location_ref.locationsId)
    result = iam.AddPolicyBindingToEkmConfig(ekm_config_name, args.member,
                                             args.role)
    iam_util.LogSetIamPolicy(ekm_config_name, 'EkmConfig')
    return result
