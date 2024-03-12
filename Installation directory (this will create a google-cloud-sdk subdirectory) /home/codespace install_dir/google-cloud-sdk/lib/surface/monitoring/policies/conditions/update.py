# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""`gcloud monitoring policies conditions update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util


class Update(base.CreateCommand):
  """Update a condition in an alerting policy."""

  @staticmethod
  def Args(parser):
    condition_arg = resource_args.CreateConditionResourceArg('update')
    resource_args.AddResourceArgs(parser, [condition_arg])
    flags.AddDisplayNameFlag(parser, 'Condition')
    flags.AddUpdateableConditionFlags(parser)

  def Run(self, args):
    util.ValidateUpdateArgsSpecified(
        args,
        ['display_name', 'trigger_count', 'trigger_percent', 'if_value'],
        'condition')

    client = policies.AlertPolicyClient()
    messages = client.messages

    condition_ref = args.CONCEPTS.condition.Parse()
    policy_ref = condition_ref.Parent()
    policy = client.Get(policy_ref)

    condition = util.GetConditionFromPolicy(condition_ref.RelativeName(),
                                            policy)
    nested_condition = condition.conditionAbsent or condition.conditionThreshold

    if args.display_name:
      condition.displayName = args.display_name

    if args.trigger_count or args.trigger_percent:
      nested_condition.trigger = messages.Trigger(
          count=args.trigger_count, percent=args.trigger_percent)

    if args.if_value is not None:
      # Copy existing condition properties into kwargs.
      kwargs = {
          'trigger_count': nested_condition.trigger.count,
          'trigger_percent': nested_condition.trigger.percent,
          'aggregations': nested_condition.aggregations,
          'duration': nested_condition.duration,
          'condition_filter': nested_condition.filter,
          'if_value': args.if_value
      }

      # If any trigger values are specified, overwrite whats in args.
      if args.trigger_count or args.trigger_percent:
        kwargs['trigger_count'] = args.trigger_count
        kwargs['trigger_percent'] = args.trigger_percent

      # Clear nested condition messages as this can potentially change.
      condition.conditionAbsent = None
      condition.conditionThreshold = None

      # This will change condition in place.
      util.BuildCondition(messages, condition=condition, **kwargs)

    return client.Update(policy_ref, policy, fields='conditions')
