# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for AI Platform operations commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log


def WaitForOpMaybe(operations_client, op, op_ref, asynchronous=False,
                   log_method=None, message=None, kind=None):
  """Waits for an operation if asynchronous flag is off.

  Args:
    operations_client: api_lib.ai.operations.OperationsClient, the client via
      which to poll.
    op: Cloud AI Platform operation, the operation to poll.
    op_ref: The operation reference to the operation resource. It's the result
      by calling resources.REGISTRY.Parse
    asynchronous: bool, whether to wait for the operation or return immediately
    log_method: Logging method used for synchronous operation. If None, no log
    message: str, the message to display while waiting for the operation.
    kind: str, the resource kind (instance, cluster, project, etc.), which will
      be passed to logging function.

  Returns:
    The result of the operation if asynchronous is true, or the Operation
      message otherwise
  """
  logging_function = {
      'create': log.CreatedResource,
      'delete': log.DeletedResource,
      'update': log.UpdatedResource,
  }
  if asynchronous:
    if logging_function.get(log_method) is not None:
      logging_function[log_method](op.name, kind=kind)
    return op
  return operations_client.WaitForOperation(
      op, op_ref, message=message).response
