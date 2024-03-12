# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""`gcloud monitoring policies conditions delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.core import log


class Delete(base.CreateCommand):
  """Delete a condition in an alerting policy.

  Delete a condition in an alerting policy. If the specified condition does
  not exist, this command will fail with an error. This will not delete
  the policy if no conditions exist.
  """

  @staticmethod
  def Args(parser):
    condition_arg = resource_args.CreateConditionResourceArg('delete')
    resource_args.AddResourceArgs(parser, [condition_arg])

  def Run(self, args):
    client = policies.AlertPolicyClient()
    condition_ref = args.CONCEPTS.condition.Parse()
    policy_ref = condition_ref.Parent()
    policy = client.Get(policy_ref)

    policy = util.RemoveConditionFromPolicy(condition_ref.RelativeName(),
                                            policy)

    response = client.Update(policy_ref, policy)
    log.DeletedResource(condition_ref.RelativeName(), 'Condition')
    return response
