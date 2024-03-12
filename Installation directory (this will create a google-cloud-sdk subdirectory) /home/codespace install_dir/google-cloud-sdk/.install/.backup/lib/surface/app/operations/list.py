# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""The `app operations list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List the operations."""

  detailed_help = {
      'EXAMPLES': """\
          To list all App Engine operations, run:

              $ {command}

          To list only 100 App Engine operations, run:

              $ {command} --limit=100

          To list only pending App Engine operations, run:

              $ {command} --pending
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--pending',
                        action='store_true',
                        default=False,
                        help='Only display pending operations')
    parser.display_info.AddFormat('table(id, start_time, status)')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    if args.pending:
      return api_client.ListOperations(op_filter='done:false')
    else:
      return api_client.ListOperations()
