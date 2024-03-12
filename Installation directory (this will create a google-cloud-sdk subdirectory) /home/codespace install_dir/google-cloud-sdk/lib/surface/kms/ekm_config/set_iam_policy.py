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
"""Set the IAM policy for EkmConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.kms import resource_args


class SetIamPolicy(base.Command):
  """Set the IAM policy for an EkmConfig.

  Sets the IAM policy for the EkmConfig in a location as defined in a JSON or
  YAML file.

  See https://cloud.google.com/iam/docs/managing-policies for details of
  the policy file format and contents.

  ## EXAMPLES
  The following command will read am IAM policy defined in a JSON file
  'policy.json' and set it for the EkmConfig with location `us-central1`:

    $ {command} policy.json --location=us-central1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')
    parser.add_argument(
        'policy_file', help=('JSON or YAML file with '
                             'the IAM policy'))

  def Run(self, args):
    messages = cloudkms_base.GetMessagesModule()

    policy, update_mask = iam_util.ParseYamlOrJsonPolicyFile(
        args.policy_file, messages.Policy)

    location_ref = args.CONCEPTS.location.Parse()
    ekm_config_name = 'projects/{0}/locations/{1}/ekmConfig'.format(
        location_ref.projectsId, location_ref.locationsId)
    result = iam.SetEkmConfigIamPolicy(ekm_config_name, policy, update_mask)
    iam_util.LogSetIamPolicy(ekm_config_name, 'EkmConfig')
    return result
