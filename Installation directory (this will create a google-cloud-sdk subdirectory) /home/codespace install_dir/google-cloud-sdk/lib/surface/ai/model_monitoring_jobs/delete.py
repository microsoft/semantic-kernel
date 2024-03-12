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
"""Vertex AI deployment monitoring jobs delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.model_monitoring_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import model_monitoring_jobs_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """
    To delete a model deployment monitoring job `123` of project `example` in region `us-central1`, run:

      $ {command} 123 --project=example --region=us-central1
    """,
}


def _Run(args, version):
  """Run method for delete command."""
  model_monitoring_job_ref = args.CONCEPTS.monitoring_job.Parse()
  region = model_monitoring_job_ref.AsDict()['locationsId']
  model_monitoring_job_id = model_monitoring_job_ref.AsDict(
  )['modelDeploymentMonitoringJobsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    console_io.PromptContinue(
        'This will delete model deployment monitoring job [{}]...'.format(
            model_monitoring_job_id),
        cancel_on_no=True)
    operation = client.ModelMonitoringJobsClient(
        version=version).Delete(model_monitoring_job_ref)
    return operations_util.WaitForOpMaybe(
        operations_client=operations.OperationsClient(),
        op=operation,
        op_ref=model_monitoring_jobs_util.ParseMonitoringJobOperation(
            operation.name))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeleteGa(base.DeleteCommand):
  """Delete an existing Vertex AI model deployment monitoring job."""

  @staticmethod
  def Args(parser):
    flags.AddModelMonitoringJobResourceArg(parser, 'to delete')

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete an existing Vertex AI model deployment monitoring job."""

  @staticmethod
  def Args(parser):
    flags.AddModelMonitoringJobResourceArg(parser, 'to delete')

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)


Delete.detailed_help = DETAILED_HELP
DeleteGa.detailed_help = DETAILED_HELP
