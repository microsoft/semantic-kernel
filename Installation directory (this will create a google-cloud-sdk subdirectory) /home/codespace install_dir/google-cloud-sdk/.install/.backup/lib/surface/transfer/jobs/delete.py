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
"""Command to delete transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import jobs_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties


class Delete(base.Command):
  """Delete a Transfer Service transfer job."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Delete a Transfer Service transfer job.
      """,
      'EXAMPLES':
          """\
      To delete job 'foo', run:

        $ {command} foo
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the job you want to delete.')

  def Run(self, args):
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    formatted_job_name = name_util.add_job_prefix(args.name)
    client.transferJobs.Delete(
        messages.StoragetransferTransferJobsDeleteRequest(
            jobName=formatted_job_name,
            projectId=properties.VALUES.core.project.Get()))
    # Display metadata of job with status updated to `DELETED`.
    return jobs_util.api_get(args.name)
