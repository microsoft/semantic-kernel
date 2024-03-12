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
"""ai-platform jobs describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import jobs_util
from googlecloudsdk.core import log


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To describe the AI Platform job named ``my-job'', run:

            {command} my-job
        """
}


def _AddDescribeArgs(parser):
  flags.JOB_NAME.AddToParser(parser)
  flags.GetSummarizeFlag().AddToParser(parser)


class Describe(base.DescribeCommand):
  """Describe an AI Platform job."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _AddDescribeArgs(parser)

  def Run(self, args):
    job = jobs_util.Describe(jobs.JobsClient(), args.job)
    self.job = job  # Hack to make the Epilog method work
    if args.summarize:
      if args.format:
        log.warning('--format is ignored when --summarize is present')
      args.format = jobs_util.GetSummaryFormat(job)
    return job

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed:
      jobs_util.PrintDescribeFollowUp(self.job.jobId)
