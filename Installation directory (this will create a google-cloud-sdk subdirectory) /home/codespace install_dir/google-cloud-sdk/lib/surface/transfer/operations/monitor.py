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
"""Command to monitor a currently running transfer operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import operations_util
from googlecloudsdk.calliope import base


class Monitor(base.Command):
  """Track progress in real time for a transfer operation."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Track progress in real time for a transfer operation.
      """,
      'EXAMPLES':
          """\
      To monitor an operation, run:

        $ {command} OPERATION-NAME

      If you're looking for specific error details, use the
      "operations describe" command:

        $ {parent_command} describe OPERATION-NAME
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name', help='The name of the operation you want to monitor.')

  def Run(self, args):
    operations_util.display_monitoring_view(args.name)
