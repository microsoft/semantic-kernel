# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Command to show details for a specified Batch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.batch import jobs
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.batch import resource_args


class Describe(base.DescribeCommand):
  """Show details of a job.

  This command can fail for the following reasons:
  * The job specified does not exist.
  * The active account does not have permission to access the given job.

  ## EXAMPLES

  To print details of the job with name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar
  """

  @staticmethod
  def Args(parser):
    resource_args.AddJobResourceArgs(parser)

  def Run(self, args):
    release_track = self.ReleaseTrack()

    client = jobs.JobsClient(release_track)
    job_ref = args.CONCEPTS.job.Parse()
    try:
      return client.Get(job_ref)
    except apitools_exceptions.HttpNotFoundError as e:
      raise exceptions.HttpException(
          e, error_format='Could not fetch resource: {status_message}.')
