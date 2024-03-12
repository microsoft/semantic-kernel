# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""api-gateway gateways list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import gateways
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List API Gateways."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list all gateways, run:

            $ {command}

          To list all gateways within the 'us-central1' location:

            $ {command} --location=us-central1
          """,
  }

  LIST_FORMAT = """
    table(
      name.segment(5):label=GATEWAY_ID,
      name.segment(3):label=LOCATION,
      displayName,
      state,
      createTime.date(),
      updateTime.date()
    )"""

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser,
                                         'gateways will be listed from',
                                         default='-',
                                         required=False)
    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(List.LIST_FORMAT)

  def Run(self, args):
    parent_ref = args.CONCEPTS.location.Parse()
    sort_by = common_args.ParseSortByArg(args.sort_by)

    return gateways.GatewayClient().List(parent_ref.RelativeName(),
                                         filters=args.filter,
                                         limit=args.limit,
                                         page_size=args.page_size,
                                         sort_by=sort_by)
