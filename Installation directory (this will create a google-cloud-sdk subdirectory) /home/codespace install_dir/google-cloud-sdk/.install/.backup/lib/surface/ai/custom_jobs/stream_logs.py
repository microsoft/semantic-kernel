# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to check stream logs of a custom job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.custom_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags as common_flags
from googlecloudsdk.command_lib.ai import log_util
from googlecloudsdk.command_lib.ai.custom_jobs import flags as custom_job_flags
from googlecloudsdk.command_lib.ai.custom_jobs import validation


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StreamLogsGA(base.Command):
  """Show stream logs from a running custom job.

    ## EXAMPLES

    To stream logs of custom job ``123'' under project ``example'' in region
    ``us-central1'', run:

      $ {command} 123 --project=example --region=us-central1
  """

  _api_version = constants.GA_VERSION

  @staticmethod
  def Args(parser):
    custom_job_flags.AddCustomJobResourceArg(parser, 'to fetch stream log')
    common_flags.AddStreamLogsFlags(parser)
    parser.display_info.AddFormat(log_util.LOG_FORMAT)

  def Run(self, args):
    custom_job_ref = args.CONCEPTS.custom_job.Parse()
    region = custom_job_ref.AsDict()['locationsId']
    validation.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._api_version, region=region):
      return log_util.StreamLogs(
          custom_job_ref.AsDict()['customJobsId'],
          continue_function=client.CustomJobsClient(
              version=self._api_version).CheckJobComplete(
                  custom_job_ref.RelativeName()),
          polling_interval=args.polling_interval,
          task_name=args.task_name,
          allow_multiline=args.allow_multiline_logs)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class StreamLogsPreGA(StreamLogsGA):
  """Show stream logs from a running custom job.

    ## EXAMPLES

    To stream logs of custom job ``123'' under project ``example'' in region
    ``us-central1'', run:

      $ {command} 123 --project=example --region=us-central1
  """
  _api_version = constants.BETA_VERSION
