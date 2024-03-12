# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Describe policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a Binary Authorization platform policy.

  ## EXAMPLES

  To delete a policy using its resource name:

    $ {command} projects/my_proj/platforms/gke/policies/policy1

  To delete the same policy using flags:

    $ {command} policy1 --platform=gke --project=my_proj
  """

  @staticmethod
  def Args(parser):
    flags.AddPlatformPolicyResourceArg(parser, 'to delete')

  def Run(self, args):
    policy_ref = args.CONCEPTS.policy_resource_name.Parse().RelativeName()
    # The API is only available in v1.
    result = platform_policy.Client('v1').Delete(policy_ref)
    log.DeletedResource(policy_ref, kind='Policy')
    return result
