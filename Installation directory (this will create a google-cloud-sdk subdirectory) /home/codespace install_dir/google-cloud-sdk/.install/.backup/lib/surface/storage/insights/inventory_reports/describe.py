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
"""Implementation of insights inventory-reports describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.insights.inventory_reports import resource_args


class Describe(base.DescribeCommand):
  """Describe an inventory report config."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe an inventory report config.
      """,
      'EXAMPLES':
          """

      To describe an inventory report config with ID=1234,
      location=us-central1, and project=foo:

        $ {command} 1234 --location=us-central1 --project=foo

      To describe the same inventory report config with fully specified name:

        $ {command} /projects/foo/locations/us-central1/reportConfigs/1234

      Describe the same inventory report config with JSON formatting, only
      returning the "displayName" field:

        $ {command} /projects/foo/locations/us-central1/reportConfigs/1234 --format="json(displayName)"
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_report_config_resource_arg(parser, 'to describe')

  def Run(self, args):
    report_config_ref = args.CONCEPTS.report_config.Parse()
    return insights_api.InsightsApi().get_inventory_report(
        report_config_ref.RelativeName()
    )
