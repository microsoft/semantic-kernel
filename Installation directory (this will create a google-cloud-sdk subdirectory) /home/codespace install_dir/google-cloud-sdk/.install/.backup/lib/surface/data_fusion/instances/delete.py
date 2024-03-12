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
"""Command to delete a Data Fusion instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import operation_poller
from googlecloudsdk.command_lib.data_fusion import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Deletes a Cloud Data Fusion instance.

  If run asynchronously with `--async`, exits after printing an operation
  that can be used to poll the status of the creation operation via:

    {command} operations list

  ## EXAMPLES

  To delete instance 'my-instance' in project 'my-project' and location
  'my-location', run:

    $ {command} --project=my-project --location=my-location my-instance
  """

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'Instance to delete.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    datafusion = df.Datafusion()
    instance_ref = args.CONCEPTS.instance.Parse()

    name = instance_ref.RelativeName()
    req = datafusion.messages.DatafusionProjectsLocationsInstancesDeleteRequest(
        name=instance_ref.RelativeName())

    console_io.PromptContinue(
        message="'{0}' will be deleted".format(name),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    operation = datafusion.client.projects_locations_instances.Delete(req)

    log.status.write('Deleting [{0}] with operation [{1}].'.format(
        instance_ref.RelativeName(), operation.name))

    if args.async_:
      return operation
    else:
      waiter.WaitFor(
          operation_poller.OperationPoller(), operation.name,
          'Waiting for [{}] to complete. This may take several minutes'.format(
              operation.name))
