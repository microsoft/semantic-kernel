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
"""Implementation of insights inventory-reports details describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.insights.inventory_reports import resource_args
from googlecloudsdk.core import log


class Describe(base.DescribeCommand):
  """Describe inventory reports detail."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe the inventory report detail.
      """,
      'EXAMPLES':
          """

      To describe an inventory report detail with ID=4568,
      location=us-central1, project=foo, and report config ID=1234:

        $ {command} 1234 --location=us-central1 --project=foo --report-config=1234

      To describe the same inventory report detail with fully specified name:

        $ {command} /projects/foo/locations/us-central1/reportConfigs/1234/reportDetails/5678

      To describe the same inventory report detail with JSON formatting, only returning
      the "status" field:

        $ {command} /projects/foo/locations/us-central1/reportConfigs/1234/reportDetails/5678 --format="json(status)"
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_report_detail_resource_arg(parser, 'to describe')

  def Run(self, args):
    report_detail_ref = args.CONCEPTS.report_detail.Parse()
    report_details = insights_api.InsightsApi().get_report_details(
        report_detail_ref.RelativeName())
    if report_details:
      log.status.Print(
          'To download the reports, use the `gcloud storage cp` command.')
      return report_details
