# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command to wait for operation completion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import operation_poller
from googlecloudsdk.command_lib.data_fusion import resource_args


class Wait(base.SilentCommand):
  """Wait for asynchronous operation to complete.

  ## EXAMPLES

  To wait for operation 'my-operation' in project 'my-project' and location
  'my-location', run:

    $ {command} --project=my-project --location=my-location my-operation
  """

  WAIT_CEILING_MS = 60 * 20 * 1000

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'The operation to wait for.')

  def Run(self, args):
    datafusion = df.Datafusion()
    operation_ref = args.CONCEPTS.operation.Parse()

    req = datafusion.messages.DatafusionProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName())

    operation = datafusion.client.projects_locations_operations.Get(req)

    waiter.WaitFor(
        operation_poller.OperationPoller(),
        operation.name,
        'Waiting for [{}] to complete.'.format(operation.name),
        wait_ceiling_ms=self.WAIT_CEILING_MS)
