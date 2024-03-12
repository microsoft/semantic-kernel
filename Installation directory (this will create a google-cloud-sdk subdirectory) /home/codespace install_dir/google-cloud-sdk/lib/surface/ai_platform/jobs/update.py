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
"""ai-platform jobs update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import jobs_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To remove all labels in the AI Platform job named ``my-job'', run:

            $ {command} my-job --clear-labels
        """
}


def _AddUpdateArgs(parser):
  """Get arguments for the `ai-platform jobs update` command."""
  flags.JOB_NAME.AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)


class Update(base.UpdateCommand):
  """Update an AI Platform job."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _AddUpdateArgs(parser)

  def Run(self, args):
    jobs_client = jobs.JobsClient()
    updated_job = jobs_util.Update(jobs_client, args)
    log.UpdatedResource(args.job, kind='ml engine job')
    return updated_job
