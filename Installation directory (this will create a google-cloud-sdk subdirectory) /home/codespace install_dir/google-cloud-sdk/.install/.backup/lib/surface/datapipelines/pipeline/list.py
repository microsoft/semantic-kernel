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
"""Command to list all the Pipelines in a given project & location."""

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
        To list all the Data Pipelines for project ``example'' in region ``us-central1'', run:

          $ {command} --project=example --region=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Pipelines in a project and location."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddUriFunc(util.GetPipelineURI)
    flags.AddRegionResourceArg(parser, 'to list pipelines')

  def Run(self, args):
    """Run the list command."""
    client = util.PipelinesClient()
    region_ref = args.CONCEPTS.region.Parse()
    return client.List(
        limit=args.limit,
        page_size=args.page_size,
        input_filter=args.filter,
        region=region_ref.RelativeName())
