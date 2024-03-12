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
"""Fetch the IAM policy for an EkmConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args


class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for an EkmConfig.

  Gets the IAM policy for the given location.

  Returns an empty policy if the resource does not have a policy set.

  ## EXAMPLES

  The following command gets the IAM policy for the EkmConfig
  within the location `us-central1`:

    $ {command} --location=us-central1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    ekm_config_name = 'projects/{0}/locations/{1}/ekmConfig'.format(
        location_ref.projectsId, location_ref.locationsId)
    return iam.GetEkmConfigIamPolicy(ekm_config_name)
