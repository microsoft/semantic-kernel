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
"""`gcloud scheduler locations list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scheduler import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scheduler import util


class List(base.ListCommand):
  """Lists the locations where Cloud Scheduler is available."""
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list the locations where Cloud Scheduler is available:

              $ {command}
         """,
  }

  @staticmethod
  def Args(parser):
    util.AddListLocationsFormats(parser)

  def Run(self, args):
    locations_client = GetApiAdapter(self.ReleaseTrack()).locations
    project_ref = util.ParseProject()
    return locations_client.List(project_ref, args.limit, args.page_size)
