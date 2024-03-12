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

"""`gcloud api-gateway operations list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List API Gateway operations."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list all Cloud API Gateway operations, run:

            $ {command}

          To list all Cloud API Gateway operations in the ``us-central1'' region, run:

            $ {command} --location=us-central1

          """
  }

  @staticmethod
  def Args(parser):
    # --sort-by and --uri are inherited for all ListCommands but are not
    # implemented here.
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    resource_args.AddLocationResourceArg(parser,
                                         'operations will be listed from',
                                         default='-')
    parser.display_info.AddFormat("""
      table(
        name.segment(5):label=OPERATION_ID,
        name.segment(3):label=LOCATION,
        done,
        metadata.requestedCancellation:label=CANCELLED,
        metadata.createTime.date(),
        metadata.verb,
        metadata.target
      )
    """)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    parent_ref = args.CONCEPTS.location.Parse()

    return operations.OperationsClient().List(parent_ref.RelativeName(),
                                              filters=args.filter,
                                              limit=args.limit,
                                              page_size=args.page_size)
