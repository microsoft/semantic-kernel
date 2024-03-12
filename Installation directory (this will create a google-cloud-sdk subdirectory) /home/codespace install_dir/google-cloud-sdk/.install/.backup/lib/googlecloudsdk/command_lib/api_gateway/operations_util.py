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

"""Utilities for interacting with Cloud API Gateway operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def PrintOperationResultWithWaitEpilogue(operation_ref, result):
  """Prints the operation result with wait epilogue.

  Args:
    operation_ref: Resource reference for the operation
    result: Epiloque string to be printed
  """

  log.status.Print("""\
{}. Use the following command to wait for its completion:

gcloud api-gateway operations wait {}
""".format(result, operation_ref.RelativeName()))


def PrintOperationResult(op_name, op_client, service=None,
                         wait_string='Waiting for long running operation',
                         async_string='Asynchronous operation is in progress',
                         is_async=False):
  """Prints results for an operation.

  Args:
    op_name: name of the operation.
    op_client: client for accessing operation data.
    service: the service which operation result can be grabbed.
    wait_string: string to use while waiting for polling operation
    async_string: string to print out for operation waiting
    is_async: whether to wait for aync operations or not.

  Returns:
    The object which is returned by the service if async is false,
    otherwise null
  """

  operation_ref = resources.REGISTRY.Parse(
      op_name,
      collection='apigateway.projects.locations.operations')

  if is_async:
    PrintOperationResultWithWaitEpilogue(operation_ref, async_string)
  else:
    return op_client.WaitForOperation(operation_ref, wait_string, service)

