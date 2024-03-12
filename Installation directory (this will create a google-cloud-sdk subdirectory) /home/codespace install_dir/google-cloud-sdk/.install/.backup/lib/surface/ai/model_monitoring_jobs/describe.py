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
"""Vertex AI model deployment monitoring jobs describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_monitoring_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags

DETAILED_HELP = {
    'EXAMPLES':
        """
    Describe a model deployment monitoring job `123` of project `example` in region `us-central1`, run:

      $ {command} 123 --project=example --region=us-central1
    """,
}


def _Run(args, version):
  """Run method for describe command."""
  model_monitoring_job_ref = args.CONCEPTS.monitoring_job.Parse()
  region = model_monitoring_job_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    return client.ModelMonitoringJobsClient(
        version=version).Get(model_monitoring_job_ref)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGa(base.DescribeCommand):
  """Get detailed model deployment monitoring job information about the given job id."""

  @staticmethod
  def Args(parser):
    flags.AddModelMonitoringJobResourceArg(parser, 'to describe')

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Get detailed model deployment monitoring job information about the given job id."""

  @staticmethod
  def Args(parser):
    flags.AddModelMonitoringJobResourceArg(parser, 'to describe')

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)


Describe.detailed_help = DETAILED_HELP
DescribeGa.detailed_help = DETAILED_HELP
