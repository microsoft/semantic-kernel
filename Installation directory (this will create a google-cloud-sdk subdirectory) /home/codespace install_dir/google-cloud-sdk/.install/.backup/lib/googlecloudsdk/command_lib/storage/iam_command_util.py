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
"""Utilities for storage surface IAM commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks import task_util


def get_single_matching_url(url_string):
  """Gets cloud resource, allowing wildcards that match only one resource."""
  if not wildcard_iterator.contains_wildcard(url_string):
    return storage_url.storage_url_from_string(url_string)

  resource_iterator = wildcard_iterator.get_wildcard_iterator(
      url_string, fields_scope=cloud_api.FieldsScope.SHORT)
  plurality_checkable_resource_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(resource_iterator)
  )

  if plurality_checkable_resource_iterator.is_plural():
    raise errors.InvalidUrlError(
        'get-iam-policy must match a single cloud resource.')
  return list(plurality_checkable_resource_iterator)[0].storage_url


def execute_set_iam_task_iterator(iterator, continue_on_error):
  """Executes single or multiple set-IAM tasks with different handling.

  Args:
    iterator (iter[set_iam_policy_task._SetIamPolicyTask]): Contains set IAM
      task(s) to execute.
    continue_on_error (bool): If multiple tasks in iterator, determines whether
      to continue executing after an error.

  Returns:
    int: Status code. For multiple tasks, the task executor will return if
      any of the tasks failed.
    object|None: If executing a single task, the newly set IAM policy. This
      is useful for outputting to the terminal.
  """
  plurality_checkable_task_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(iterator))

  if not plurality_checkable_task_iterator.is_plural():
    # Underlying iterator should error if no matches, so this means there is a
    # single match. Output its new policy to match other IAM set commands.
    return 0, task_util.get_first_matching_message_payload(
        next(plurality_checkable_task_iterator).execute().messages,
        task.Topic.SET_IAM_POLICY)

  task_status_queue = task_graph_executor.multiprocessing_context.Queue()
  exit_code = task_executor.execute_tasks(
      plurality_checkable_task_iterator,
      parallelizable=True,
      task_status_queue=task_status_queue,
      progress_manager_args=task_status.ProgressManagerArgs(
          increment_type=task_status.IncrementType.INTEGER, manifest_path=None),
      continue_on_error=continue_on_error)
  return exit_code, None


def add_iam_binding_to_resource(args, url, messages, policy, task_type):
  """Extracts new binding from args and applies to existing policy.

  Args:
    args (argparse Args): Contains flags user ran command with.
    url (CloudUrl): URL of target resource, already validated for type.
    messages (object): Must contain IAM data types needed to create new policy.
    policy (object): Existing IAM policy on target to update.
    task_type (set_iam_policy_task._SetIamPolicyTask): The task instance to use
      to execute the iam binding change.

  Returns:
    object: The updated IAM policy set in the cloud.
  """
  condition = iam_util.ValidateAndExtractCondition(args)
  iam_util.AddBindingToIamPolicyWithCondition(
      messages.Policy.BindingsValueListEntry, messages.Expr, policy,
      args.member, args.role, condition)

  task_output = task_type(url, policy).execute()
  return task_util.get_first_matching_message_payload(task_output.messages,
                                                      task.Topic.SET_IAM_POLICY)


def remove_iam_binding_from_resource(args, url, policy, task_type):
  """Extracts binding from args and removes it from existing policy.

  Args:
    args (argparse Args): Contains flags user ran command with.
    url (CloudUrl): URL of target resource, already validated for type.
    policy (object): Existing IAM policy on target to update.
    task_type (set_iam_policy_task._SetIamPolicyTask): The task instance to use
      to execute the iam binding change.

  Returns:
    object: The updated IAM policy set in the cloud.
  """
  condition = iam_util.ValidateAndExtractCondition(args)
  iam_util.RemoveBindingFromIamPolicyWithCondition(policy, args.member,
                                                   args.role, condition,
                                                   args.all)

  task_output = task_type(url, policy).execute()
  return task_util.get_first_matching_message_payload(task_output.messages,
                                                      task.Topic.SET_IAM_POLICY)
