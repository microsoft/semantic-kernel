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
"""Command to monitor the last operation of a transfer job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import jobs_util
from googlecloudsdk.api_lib.transfer import operations_util
from googlecloudsdk.calliope import base


class Monitor(base.Command):
  """Track progress in real time for a transfer job's latest operation."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Track progress in real time for a transfer job's latest operation.
      """,
      'EXAMPLES':
          """\
      To monitor a job, run:

        $ {command} JOB-NAME

      If you're looking for recent error details, use the "Operation name"
      returned by this command as input to the "operations describe" command:

        $ {command} JOB-NAME

        $ {grandparent_command} operations describe OPERATION-NAME
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name',
        help='The name of the job you want to monitor'
        " (you'll see details for the job's latest operation).")

  def Run(self, args):
    operation_name = jobs_util.block_until_operation_created(args.name)
    operations_util.display_monitoring_view(operation_name)
