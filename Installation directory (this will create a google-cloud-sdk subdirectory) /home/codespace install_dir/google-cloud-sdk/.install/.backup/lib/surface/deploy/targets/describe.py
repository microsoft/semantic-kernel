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
"""Describes a Gcloud Deploy target resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import describe
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import resource_args

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
    To describe a target called 'test' for delivery pipeline 'test-pipeline' in region 'us-central1', run:

       $ {command} test --delivery-pipeline=test-pipeline --region=us-central1

  """,
}


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  resource_args.AddTargetResourceArg(parser, positional=True)
  flags.AddDeliveryPipeline(parser, required=False)
  flags.AddListAllPipelines(parser)
  flags.AddSkipPipelineLookup(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describes details specific to the individual target, delivery pipeline qualified.

  The output contains four sections:

  Target:

    detail of the target to be described.

  Latest Release:

    the detail of the active release in the target.

  Latest Rollout:

    the detail of the active rollout in the target.

  Deployed:

    timestamp of the last successful deployment.

  Pending Approvals:

    list of the rollouts that require approval.
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
    target_ref = args.CONCEPTS.target.Parse()

    return describe.DescribeTarget(target_ref, args.delivery_pipeline,
                                   args.skip_pipeline_lookup,
                                   args.list_all_pipelines)
