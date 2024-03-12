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
"""Command to describe a Data Fusion instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import operation_poller
from googlecloudsdk.command_lib.data_fusion import resource_args
from googlecloudsdk.core import log


class Restart(base.DescribeCommand):
  """Restarts a Cloud Data Fusion instance."""
  detailed_help = {
      'DESCRIPTION': """\
       If run asynchronously with `--async`, exits after printing an operation
       that can be used to poll the status of the creation operation via:

         {command} operations list
          """,
      'EXAMPLES': """\
        To restart instance 'my-instance' in project 'my-project' and location
        'my-location', run:

          $ {command} --project=my-project --location=my-location my-instance
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'Instance to restart.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    datafusion = df.Datafusion()
    instance_ref = args.CONCEPTS.instance.Parse()

    request = datafusion.messages.DatafusionProjectsLocationsInstancesRestartRequest(
        name=instance_ref.RelativeName())

    operation = datafusion.client.projects_locations_instances.Restart(request)

    if args.async_:
      log.CreatedResource(
          instance_ref.RelativeName(), kind='instance', is_async=True)
      return operation
    else:
      waiter.WaitFor(
          operation_poller.OperationPoller(),
          operation.name,
          'Waiting for [{}] to complete. This may take several minutes.'.format(
              operation.name),
          wait_ceiling_ms=df.OPERATION_TIMEOUT)
      log.ResetResource(
          instance_ref.RelativeName(), kind='instance', is_async=False)
