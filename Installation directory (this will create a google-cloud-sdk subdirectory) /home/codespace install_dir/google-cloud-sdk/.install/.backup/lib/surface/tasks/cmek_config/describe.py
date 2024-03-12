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
"""`gcloud tasks cmek-config describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class GetCmekConfig(base.Command):
  """Get CMEK configuration for Cloud Tasks in the specified location."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To get a CMEK config:

              $ {command} --location=my-location
         """,
  }

  @staticmethod
  def Args(parser):
    flags.DescribeCmekConfigResourceFlag(parser)

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    cmek_config_client = api.cmek_config
    project_id, location_id = parsers.ParseKmsDescribeArgs(args)

    cmek_config = cmek_config_client.GetCmekConfig(project_id, location_id)
    return cmek_config
