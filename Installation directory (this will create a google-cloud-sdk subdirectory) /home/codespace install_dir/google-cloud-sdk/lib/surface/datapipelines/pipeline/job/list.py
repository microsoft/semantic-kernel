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
"""Command to list all the Jobs in a given Pipeline."""

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
        To list all the jobs within a pipeline ``pipeline-1'' in project ``project-1'' and region ``us-central1'', run:

          $ {command} --pipeline=pipeline-1 --project=project-1 --region=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Jobs within a pipeline in a specific project and region."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddUriFunc(util.GetJobURI)
    flags.AddListJobsFlags(parser)

  def Run(self, args):
    """Run the list command."""
    client = util.JobsClient()
    pipeline_ref = args.CONCEPTS.pipeline.Parse()
    return client.List(
        limit=args.limit,
        page_size=args.page_size,
        pipeline=pipeline_ref.RelativeName())
