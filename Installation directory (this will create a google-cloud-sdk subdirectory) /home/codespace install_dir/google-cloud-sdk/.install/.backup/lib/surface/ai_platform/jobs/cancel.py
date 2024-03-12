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
"""ai-platform jobs cancel command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import jobs_util


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To cancel a running AI Platform job named ``my-job'', run:

            $ {command} my-job
        """
}


def _AddCancelArgs(parser):
  flags.JOB_NAME.AddToParser(parser)


class Cancel(base.SilentCommand):
  """Cancel a running AI Platform job."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _AddCancelArgs(parser)

  def Run(self, args):
    return jobs_util.Cancel(jobs.JobsClient(), args.job)


_DETAILED_HELP = {
    'DESCRIPTION':
        """\
*{command}* cancels a running AI Platform job. If the job is already
finished, the command will not perform an operation and exit successfully.
"""
}


Cancel.detailed_help = _DETAILED_HELP
