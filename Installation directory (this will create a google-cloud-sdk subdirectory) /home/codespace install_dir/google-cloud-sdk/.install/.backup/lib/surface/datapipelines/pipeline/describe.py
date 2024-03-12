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
"""Command to describe a Pipeline for the Data Pipelines API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datapipelines import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datapipelines import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To describe a Data Pipeline ``PIPELINE_NAME'' of project ``example'' in region ``us-central1'', run:

          $ {command} PIPELINE_NAME --project=example --region=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe Data Pipelines Pipeline."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribePipelineFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = util.PipelinesClient()
    pipelines_ref = args.CONCEPTS.pipeline.Parse()
    return client.Describe(pipeline=pipelines_ref.RelativeName())
