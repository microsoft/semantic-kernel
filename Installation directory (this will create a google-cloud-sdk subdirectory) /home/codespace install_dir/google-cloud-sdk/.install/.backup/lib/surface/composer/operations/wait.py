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
"""Command to wait for operation completion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To wait for the asynchronous operation ``operation-1'' in the
          location ``us-central1'' to complete, run:

            $ {command} operation-1 --location=us-central1
        """
}


class Wait(base.SilentCommand):
  """Wait for asynchronous operation to complete."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'to wait for')

  def Run(self, args):
    operation_ref = args.CONCEPTS.operation.Parse()
    operation = operations_api_util.Get(
        operation_ref, release_track=self.ReleaseTrack())
    operations_api_util.WaitForOperation(
        operation,
        'Waiting for [{}] to complete.'.format(operation.name),
        release_track=self.ReleaseTrack())
