# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""ai-platform jobs stream-logs command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import jobs_util
from googlecloudsdk.command_lib.ml_engine import log_utils
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To show the logs from running the AI Platform job ``my-job'', run:

            $ {command} my-job
        """
}


def _AddStreamLogsArgs(parser):
  flags.JOB_NAME.AddToParser(parser)
  flags.POLLING_INTERVAL.AddToParser(parser)
  flags.ALLOW_MULTILINE_LOGS.AddToParser(parser)
  flags.TASK_NAME.AddToParser(parser)


class StreamLogs(base.Command):
  """Show logs from a running AI Platform job."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _AddStreamLogsArgs(parser)
    parser.display_info.AddFormat(log_utils.LOG_FORMAT)

  def Run(self, args):
    """Run the stream-logs command."""
    return jobs_util.StreamLogs(
        args.job, args.task_name,
        properties.VALUES.ml_engine.polling_interval.GetInt(),
        args.allow_multiline_logs)
