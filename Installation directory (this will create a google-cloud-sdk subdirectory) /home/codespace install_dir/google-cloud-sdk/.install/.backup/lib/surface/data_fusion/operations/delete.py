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
"""Command to delete an operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a completed Data Fusion operation.

  ## EXAMPLES

  To delete operation 'my-operation' in project 'my-project' and location
  'my-location', run:

    $ {command} --project=my-project --location=my-location my-operation
  """

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'The operation to delete.')

  def Run(self, args):
    datafusion = df.Datafusion()
    op_ref = args.CONCEPTS.operation.Parse()

    console_io.PromptContinue(
        message="'{0}' will be deleted".format(op_ref.Name()),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.',
        throw_if_unattended=True)

    req = datafusion.messages.DatafusionProjectsLocationsOperationsDeleteRequest(
        name=op_ref.RelativeName())

    datafusion.client.projects_locations_operations.Delete(req)

    log.DeletedResource(op_ref.RelativeName(), kind='operation')
