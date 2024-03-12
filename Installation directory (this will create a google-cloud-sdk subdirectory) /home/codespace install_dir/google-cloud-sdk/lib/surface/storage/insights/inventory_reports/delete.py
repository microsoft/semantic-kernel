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
"""Implementation command for deleting inventory report configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.insights.inventory_reports import resource_args
from googlecloudsdk.core import log


class Delete(base.Command):
  """Delete an inventory report config."""

  detailed_help = {
      'DESCRIPTION':
          """
      Delete an inventory report config.
      """,
      'EXAMPLES':
          """
      To delete an inventory report config with ID=1234,
      location=us-central1 and project=foo:

        $ {command} 1234 --location=us-central1 --project=foo

      To delete the same inventory report config with fully specified name:

        $ {command} /projects/foo/locations/us-central1/reportConfigs/1234

      To delete the report config with all generated report details:

        $ {command} /projects/foo/locations/us-central1/reportConfigs/1234 --force
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_report_config_resource_arg(parser, 'to delete')
    parser.add_argument(
        '--force',
        action='store_true',
        help='If set, all report details for this report config'
        ' will be deleted.'
    )

  def Run(self, args):
    report_config_name = args.CONCEPTS.report_config.Parse().RelativeName()
    insights_api.InsightsApi().delete_inventory_report(
        report_config_name, args.force
    )
    log.status.Print('Deleted report config: {}'.format(
        report_config_name))
