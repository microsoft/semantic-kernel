# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""`gcloud app runtimes list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the available runtimes.

  This command lists all the available runtimes and their current stages, for
  example,
  GA, BETA or END OF SUPPORT.
  """

  detailed_help = {
      'EXAMPLES': """\
          To list all the runtimes in the App Engine standard environment, run:

            $ {command} --environment=standard

          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--environment',
        required=True,
        choices=['standard'],
        help='Environment for the application.',
    )
    parser.display_info.AddFormat("""
      table(
        name,
        stage,
        environment
      )
    """)

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    environment = (
        api_client.messages.AppengineAppsListRuntimesRequest.EnvironmentValueValuesEnum.STANDARD
    )
    if args.environment == 'standard':
      environment = (
          api_client.messages.AppengineAppsListRuntimesRequest.EnvironmentValueValuesEnum.STANDARD
      )
    response = api_client.ListRuntimes(environment)
    return [Runtime(r) for r in response.runtimes]


class Runtime:
  """Runtimes wrapper for ListRuntimesResponse#Runtimes.

  Attributes:
    name: A string name of the runtime.
    stage: An enum of the release state of the runtime, e.g., GA, BETA, etc.
    environment: Environment of the runtime.
  """

  def __init__(self, runtime):
    self.name = runtime.name
    self.stage = runtime.stage
    self.environment = runtime.environment
