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
"""ai-platform jobs list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import jobs_util


_DEFAULT_FORMAT = """
        table(
            jobId.basename(),
            state:label=STATUS,
            createTime.date(tz=LOCAL):label=CREATED
         )
    """

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To list the existing AI Platform jobs, run:

            $ {command}
        """
}


class List(base.ListCommand):
  """List existing AI Platform jobs."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_DEFAULT_FORMAT)

  def Run(self, args):
    return jobs_util.List(jobs.JobsClient())
