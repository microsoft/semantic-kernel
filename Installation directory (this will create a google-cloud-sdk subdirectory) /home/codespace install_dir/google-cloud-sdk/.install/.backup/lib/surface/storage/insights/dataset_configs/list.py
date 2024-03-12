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

"""Implementation of list command for Insights dataset config."""

import re

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags

LOCATION_REGEX_PATTERN = re.compile(r'locations/(.*)/.*/')


def _transform_location(dataset_config):
  matched_result = re.search(LOCATION_REGEX_PATTERN, dataset_config['name'])
  if matched_result and matched_result.group(1) is not None:
    return matched_result.group(1)
  else:
    return 'N/A-Misformated Value'


_TRANSFORMS = {'location_transform': _transform_location}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List returns all the Insights dataset configs for given location."""

  detailed_help = {
      'DESCRIPTION': """
      List Cloud storage Insights dataset configs.
      """,
      'EXAMPLES': """

      List all dataset configs in all locations:

          $ {command}

      List all dataset configs for location "us-central1":

          $ {command} --location=us-central1

      List all dataset configs with a page size of "20":

          $ {command} --location=us-central1 --page-size=20

      List all dataset configs with JSON formatting:

          $ {command} --location=us-central1 --format=json
      """,
  }

  @staticmethod
  def Args(parser):
    flags.add_dataset_config_location_flag(parser, is_required=False)
    parser.display_info.AddFormat("""
        table(
            uid:label=DATASET_CONFIG_ID,
            name.basename():label=DATASET_CONFIG_NAME,
            location_transform():label=LOCATION,
            sourceProjects.projectNumbers:label=SOURCE_PROJECTS,
            organizationNumber:label=ORGANIZATION_NUMBER,
            retentionPeriodDays:label=RETENTION_PERIOD_DAYS,
            datasetConfigState:label=STATE
        )
        """)
    parser.display_info.AddTransforms(_TRANSFORMS)

  def Run(self, args):
    return insights_api.InsightsApi().list_dataset_config(
        location=args.location, page_size=args.page_size
    )
