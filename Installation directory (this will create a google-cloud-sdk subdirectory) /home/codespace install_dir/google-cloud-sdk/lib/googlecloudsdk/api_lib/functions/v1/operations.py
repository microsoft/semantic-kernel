# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""A library used to interact with Operations objects."""
# TODO(b/73491568) Refactor to use api_lib.util.waiter

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import exceptions
from googlecloudsdk.core.console import progress_tracker as console_progress_tracker
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import retry

MAX_WAIT_MS = 1820000
WAIT_CEILING_MS = 2000
SLEEP_MS = 1000


def OperationErrorToString(error):
  """Returns a human readable string representation from the operation.

  Args:
    error: A string representing the raw json of the operation error.

  Returns:
    A human readable string representation of the error.
  """
  return 'OperationError: code={0}, message={1}'.format(
      error.code, encoding.Decode(error.message)
  )


# TODO(b/130604453): Remove try_set_invoker option.
def _GetOperationStatus(
    client,
    get_request,
    progress_tracker=None,
    try_set_invoker=None,
    on_every_poll=None,
):
  """Helper function for getting the status of an operation.

  Args:
    client: The client used to make requests.
    get_request: A GetOperationRequest message.
    progress_tracker: progress_tracker.ProgressTracker, A reference for the
      progress tracker to tick, in case this function is used in a Retryer.
    try_set_invoker: function to try setting invoker, see above TODO.
    on_every_poll: list of functions to execute every time we poll. Functions
      should take in Operation as an argument.

  Returns:
    True if the operation succeeded without error.
    False if the operation is not yet done.

  Raises:
    FunctionsError: If the operation is finished with error.
  """
  if try_set_invoker:
    try_set_invoker()
  if progress_tracker:
    progress_tracker.Tick()
  op = client.operations.Get(get_request)
  if op.error:
    raise exceptions.FunctionsError(OperationErrorToString(op.error))
  if on_every_poll:
    for function in on_every_poll:
      function(op)
  return op.done


# TODO(b/139026575): Remove try_set_invoker option.
def _WaitForOperation(
    client, get_request, message, try_set_invoker=None, on_every_poll=None
):
  """Wait for an operation to complete.

  No operation is done instantly. Wait for it to finish following this logic:
  * we wait 1s (jitter is also 1s)
  * we query service
  * if the operation is not finished we loop to first point
  * wait limit is 1820s - if we get to that point it means something is wrong
        and we can throw an exception

  Args:
    client:  The client used to make requests.
    get_request: A GetOperationRequest message.
    message: str, The string to print while polling.
    try_set_invoker: function to try setting invoker, see above TODO.
    on_every_poll: list of functions to execute every time we poll. Functions
      should take in Operation as an argument.

  Returns:
    True if the operation succeeded without error.

  Raises:
    FunctionsError: If the operation takes more than 1820s.
  """

  with console_progress_tracker.ProgressTracker(message, autotick=False) as pt:
    # This is actually linear retryer.
    retryer = retry.Retryer(
        exponential_sleep_multiplier=1,
        max_wait_ms=MAX_WAIT_MS,
        wait_ceiling_ms=WAIT_CEILING_MS,
    )
    try:
      retryer.RetryOnResult(
          _GetOperationStatus,
          [client, get_request],
          {
              'progress_tracker': pt,
              'try_set_invoker': try_set_invoker,
              'on_every_poll': on_every_poll,
          },
          should_retry_if=lambda done, _: not done,
          sleep_ms=SLEEP_MS,
      )
    except retry.WaitException:
      raise exceptions.FunctionsError(
          'Operation {0} is taking too long'.format(get_request.name)
      )


def Wait(
    operation,
    messages,
    client,
    notice=None,
    try_set_invoker=None,
    on_every_poll=None,
):
  """Initialize waiting for operation to finish.

  Generate get request based on the operation and wait for an operation
  to complete.

  Args:
    operation: The operation which we are waiting for.
    messages: GCF messages module.
    client: GCF client module.
    notice: str, displayed when waiting for the operation to finish.
    try_set_invoker: function to try setting invoker, see above TODO.
    on_every_poll: list of functions to execute every time we poll. Functions
      should take in Operation as an argument.

  Raises:
    FunctionsError: If the operation takes more than 620s.
  """
  if notice is None:
    notice = 'Waiting for operation to finish'
  request = messages.CloudfunctionsOperationsGetRequest()
  request.name = operation.name
  _WaitForOperation(client, request, notice, try_set_invoker, on_every_poll)
