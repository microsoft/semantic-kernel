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
"""Describes a Gcloud Deploy delivery pipeline resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import delivery_pipeline
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import describe
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
  To describe a delivery pipeline called 'test-pipeline' in region 'us-central1', run:

     $ {command} test-pipeline --region=us-central1

""",
}


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  resource_args.AddDeliveryPipelineResourceArg(parser, positional=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Show details about a delivery pipeline.

  The output contains the following sections:

  Delivery Pipeline:

    - detail of the delivery pipeline to be described.

  Targets:

    - target name.

    - active release in the target.

    - timestamp of the last successful deployment.

    - list of the rollouts that require approval.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    """This is what gets called when the user runs this command."""
    pipeline_ref = args.CONCEPTS.delivery_pipeline.Parse()
    # Check if the pipeline exists.
    pipeline = delivery_pipeline.DeliveryPipelinesClient().Get(
        pipeline_ref.RelativeName()
    )
    output = {'Delivery Pipeline': pipeline}
    region = pipeline_ref.AsDict()['locationsId']
    targets = []
    # output the deployment status of the targets in the pipeline.
    for stage in pipeline.serialPipeline.stages:
      target_ref = target_util.TargetReference(
          stage.targetId,
          pipeline_ref.AsDict()['projectsId'], region)
      try:
        target_obj = target_util.GetTarget(target_ref)
      except apitools_exceptions.HttpError as error:
        log.debug('Failed to get target {}: {}'.format(stage.targetId, error))
        log.status.Print('Unable to get target {}'.format(stage.targetId))
        continue
      detail = {'Target': target_ref.RelativeName()}
      current_rollout = target_util.GetCurrentRollout(target_ref, pipeline_ref)
      detail = describe.SetCurrentReleaseAndRollout(current_rollout, detail)
      if target_obj.requireApproval:
        detail = describe.ListPendingApprovals(target_ref, pipeline_ref, detail)
      targets.append(detail)

    output['Targets'] = targets

    return output
