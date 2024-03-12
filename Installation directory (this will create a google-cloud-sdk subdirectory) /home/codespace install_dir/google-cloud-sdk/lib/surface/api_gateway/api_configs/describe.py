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
"""`gcloud api-gateway api-configs describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import api_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Show details about a specific API config."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To show details about an API config, run:

          $ {command} my-config --api=my-api
        """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--view',
        default='BASIC',
        choices=['BASIC', 'FULL'],
        help="""\
      The API Configuration view to return. If \
      'FULL' is specified, the base64 encoded API Configuration's source file \
      conent will be included in the response.
      """)
    resource_args.AddApiConfigResourceArg(parser, 'created', positional=True)

  def Run(self, args):
    config_ref = args.CONCEPTS.api_config.Parse()

    return api_configs.ApiConfigClient().Get(config_ref, args.view)
