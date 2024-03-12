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

"""Batches submit command utility."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.api_lib.dataproc.poller import batch_poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.dataproc.batches import (
    batches_create_request_factory)
from googlecloudsdk.core import log


def Submit(batch_workload_message, dataproc, args):
  """Submits a batch workload.

  Submits a batch workload and streams output if necessary.
  Make sure the parsed argument contains all the necessary arguments before
  calling. It should be fine if the arg parser was passed to
  BatchesCreateRequestFactory's AddArguments function previously.

  Args:
    batch_workload_message: A batch workload message. For example, a SparkBatch
    instance.
    dataproc: An api_lib.dataproc.Dataproc instance.
    args: Parsed arguments.

  Returns:
    Remote return value for a BatchesCreate request.
  """
  request = batches_create_request_factory.BatchesCreateRequestFactory(
      dataproc).GetRequest(args, batch_workload_message)
  batch_op = dataproc.client.projects_locations_batches.Create(request)

  log.status.Print('Batch [{}] submitted.'.format(request.batchId))
  metadata = util.ParseOperationJsonMetadata(
            batch_op.metadata, dataproc.messages.BatchOperationMetadata)
  for warning in metadata.warnings:
    log.warning(warning)

  if not args.async_:
    poller = batch_poller.BatchPoller(dataproc)
    waiter.WaitFor(
        poller,
        '{}/batches/{}'.format(request.parent, request.batchId),
        max_wait_ms=sys.maxsize,
        sleep_ms=5000,
        wait_ceiling_ms=5000,
        exponential_sleep_multiplier=1.,
        custom_tracker=None,
        tracker_update_func=poller.TrackerUpdateFunction)
    log.status.Print('Batch [{}] finished.'.format(request.batchId))

  return batch_op
